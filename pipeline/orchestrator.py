"""
Pipeline Orchestrator — end-to-end ranking pipeline.

Two modes:
1. Pre-computation: embed all candidates, save artifacts to disk
2. Ranking: load artifacts, score, rank, generate reasoning, output CSV

The ranking step must complete in <5 minutes on CPU with 16GB RAM and no network.
"""

from __future__ import annotations

import time
import csv
from pathlib import Path

import numpy as np

from api.schemas.candidate import CandidateData
from api.schemas.result import RankedCandidate, Shortlist
from config.settings import ARTIFACTS_DIR, TOP_K_RETRIEVAL, TOP_N_OUTPUT
from pipeline.embedding.candidate_embedder import build_candidate_texts_batch
from pipeline.embedding.embedder import EmbeddingService
from pipeline.embedding.jd_embedder import embed_jd
from pipeline.ingestion.candidate_parser import load_candidates
from pipeline.retrieval.retriever import CandidateRetriever
from pipeline.scoring.behavioral_scorer import score_behavioral
from pipeline.scoring.career_scorer import score_career
from pipeline.scoring.honeypot_detector import detect_honeypot
from pipeline.scoring.hybrid_scorer import compute_hybrid_score
from pipeline.scoring.skill_scorer import score_skills
from pipeline.explanation.explainer import generate_reasoning


class RankingPipeline:
    """End-to-end candidate ranking pipeline."""

    def __init__(self, role_type: str = "startup"):
        self.role_type = role_type
        self._embedding_service = None

    @property
    def embedding_service(self) -> EmbeddingService:
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    # ─── Pre-computation Phase ───────────────────────────────────────────

    def precompute(
        self,
        candidates_path: str | Path,
        output_dir: str | Path = ARTIFACTS_DIR,
        limit: int | None = None,
    ) -> None:
        """
        Pre-compute embeddings and save artifacts to disk.

        This step can take time and uses the embedding model.
        It runs ONCE before the ranking step.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        print("=" * 60)
        print("PRE-COMPUTATION PHASE")
        print("=" * 60)

        # Step 1: Load candidates
        print("\n[1/4] Loading candidates...")
        t0 = time.time()
        candidates = load_candidates(candidates_path, limit=limit)
        print(f"  Loaded in {time.time() - t0:.1f}s")

        # Step 2: Save candidate IDs for index alignment
        print("\n[2/4] Saving candidate IDs...")
        candidate_ids = [c.candidate_id for c in candidates]
        with open(output_dir / "candidate_ids.txt", "w") as f:
            for cid in candidate_ids:
                f.write(cid + "\n")

        # Step 3: Embed JD
        print("\n[3/4] Embedding JD...")
        t0 = time.time()
        jd_embedding = embed_jd(self.embedding_service)
        np.save(output_dir / "jd_embedding.npy", jd_embedding)
        print(f"  JD embedded in {time.time() - t0:.1f}s (dim={jd_embedding.shape[0]})")

        # Step 4: Embed all candidates
        print(f"\n[4/4] Embedding {len(candidates)} candidates...")
        t0 = time.time()
        candidate_texts = build_candidate_texts_batch(candidates)
        candidate_embeddings = self.embedding_service.embed_batch(
            candidate_texts,
            show_progress=True,
        )
        np.save(output_dir / "candidate_embeddings.npy", candidate_embeddings)
        print(f"  Embedded in {time.time() - t0:.1f}s (shape={candidate_embeddings.shape})")

        print(f"\nArtifacts saved to {output_dir}")
        print("Pre-computation complete.")

    # ─── Ranking Phase ───────────────────────────────────────────────────

    def rank(
        self,
        candidates_path: str | Path,
        artifacts_dir: str | Path = ARTIFACTS_DIR,
        output_path: str | Path | None = None,
        limit: int | None = None,
        top_n: int = TOP_N_OUTPUT,
    ) -> Shortlist:
        """
        Run the full ranking pipeline.

        This must complete in <5 minutes on CPU with no network.

        Steps:
        1. Load candidates + pre-computed artifacts
        2. Semantic retrieval (top-K by cosine similarity)
        3. Multi-signal scoring on top-K candidates
        4. Hybrid blend → final score
        5. Generate reasoning
        6. Output CSV
        """
        artifacts_dir = Path(artifacts_dir)

        print("=" * 60)
        print("RANKING PHASE")
        print("=" * 60)
        pipeline_start = time.time()

        # ── Step 1: Load data ────────────────────────────────────────────
        print("\n[1/6] Loading candidates and artifacts...")
        t0 = time.time()
        candidates = load_candidates(candidates_path, limit=limit)
        cand_map = {c.candidate_id: c for c in candidates}

        # Load pre-computed embeddings
        jd_embedding = np.load(artifacts_dir / "jd_embedding.npy")
        candidate_embeddings = np.load(artifacts_dir / "candidate_embeddings.npy")

        # Load candidate IDs (for alignment with embeddings)
        with open(artifacts_dir / "candidate_ids.txt", "r") as f:
            embedding_ids = [line.strip() for line in f if line.strip()]

        print(f"  Loaded in {time.time() - t0:.1f}s")

        # ── Step 2: Semantic retrieval ───────────────────────────────────
        print(f"\n[2/6] Semantic retrieval (top-{TOP_K_RETRIEVAL} from {len(embedding_ids)})...")
        t0 = time.time()
        retriever = CandidateRetriever(candidate_embeddings, embedding_ids)
        semantic_scores = retriever.retrieve_all_scores(jd_embedding)
        # Get top-K for detailed scoring
        top_k_results = retriever.retrieve(jd_embedding, top_k=TOP_K_RETRIEVAL)
        top_k_ids = {cid for cid, _ in top_k_results}
        print(f"  Retrieved in {time.time() - t0:.2f}s")

        # ── Step 3: Honeypot detection (on full pool) ────────────────────
        print("\n[3/6] Detecting honeypots...")
        t0 = time.time()
        honeypot_map: dict[str, tuple[bool, list[str]]] = {}
        honeypot_count = 0
        for cand in candidates:
            is_hp, reasons = detect_honeypot(cand)
            honeypot_map[cand.candidate_id] = (is_hp, reasons)
            if is_hp:
                honeypot_count += 1
        print(f"  Detected {honeypot_count} honeypots in {time.time() - t0:.1f}s")

        # ── Step 4: Multi-signal scoring (on top-K) ──────────────────────
        print(f"\n[4/6] Scoring {len(top_k_ids)} candidates...")
        t0 = time.time()
        scored_candidates: list[tuple[str, float, dict]] = []

        for cid in top_k_ids:
            if cid not in cand_map:
                continue

            cand = cand_map[cid]
            is_hp, hp_reasons = honeypot_map.get(cid, (False, []))

            # Get semantic score
            sem_score = semantic_scores.get(cid, 0.0)
            # Normalize to 0-1 (cosine sim can be negative)
            sem_score = max(0.0, min(1.0, (sem_score + 1.0) / 2.0))

            # Career fit
            career_s, career_details = score_career(cand)

            # Skill match
            skill_s, skill_details = score_skills(cand)

            # Behavioral signals
            behavioral_s, behavioral_details = score_behavioral(cand)

            # Hybrid blend
            final_score, breakdown = compute_hybrid_score(
                candidate=cand,
                semantic_score=sem_score,
                career_score=career_s,
                skill_score=skill_s,
                behavioral_score=behavioral_s,
                is_honeypot=is_hp,
                role_type=self.role_type,
            )

            scored_candidates.append((cid, final_score, {
                "breakdown": breakdown,
                "is_honeypot": is_hp,
                "honeypot_reasons": hp_reasons,
            }))

        # Sort by score descending
        scored_candidates.sort(key=lambda x: -x[1])
        print(f"  Scored in {time.time() - t0:.1f}s")

        # ── Step 5: Generate reasoning for top-N ─────────────────────────
        print(f"\n[5/6] Generating reasoning for top {top_n}...")
        t0 = time.time()
        ranked_list: list[RankedCandidate] = []

        for rank_idx, (cid, score, meta) in enumerate(scored_candidates[:top_n], start=1):
            cand = cand_map[cid]
            breakdown = meta["breakdown"]
            is_hp = meta["is_honeypot"]
            hp_reasons = meta["honeypot_reasons"]

            reasoning = generate_reasoning(
                candidate=cand,
                rank=rank_idx,
                score=score,
                breakdown=breakdown,
                is_honeypot=is_hp,
                honeypot_reasons=hp_reasons,
            )

            ranked_list.append(RankedCandidate(
                candidate_id=cid,
                rank=rank_idx,
                score=round(score, 4),
                breakdown=breakdown,
                reasoning=reasoning,
                is_honeypot=is_hp,
                name=cand.profile.anonymized_name,
                current_title=cand.profile.current_title,
                years_of_experience=cand.profile.years_of_experience,
            ))

        print(f"  Generated in {time.time() - t0:.1f}s")

        # ── Step 6: Output CSV ───────────────────────────────────────────
        total_time = time.time() - pipeline_start
        shortlist = Shortlist(
            candidates=ranked_list,
            total_evaluated=len(candidates),
            honeypots_detected=honeypot_count,
            latency_ms=total_time * 1000,
        )

        if output_path:
            self._write_csv(ranked_list, output_path)

        print(f"\n{'=' * 60}")
        print(f"RANKING COMPLETE")
        print(f"  Total candidates: {len(candidates)}")
        print(f"  Honeypots filtered: {honeypot_count}")
        print(f"  Top-{top_n} ranked in {total_time:.1f}s")
        print(f"  #1: {ranked_list[0].name} ({ranked_list[0].current_title}) — {ranked_list[0].score}")
        if output_path:
            print(f"  CSV saved to: {output_path}")
        print(f"{'=' * 60}")

        return shortlist

    def _write_csv(self, ranked: list[RankedCandidate], path: str | Path) -> None:
        """Write the submission CSV in the required format."""
        path = Path(path)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["candidate_id", "rank", "score", "reasoning"])
            for r in ranked:
                writer.writerow([r.candidate_id, r.rank, f"{r.score:.4f}", r.reasoning])
