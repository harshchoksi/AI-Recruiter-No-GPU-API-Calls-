"""Deeper honeypot investigation - find the ~80 actual honeypots."""
import json
from collections import Counter

candidates = []
with open(r'[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\candidates.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            candidates.append(json.loads(line))

print(f"Total candidates: {len(candidates)}\n")

# Now let's look at actual honeypot detection from our code
import sys
sys.path.insert(0, '.')
from api.schemas.candidate import CandidateData
from pipeline.scoring.honeypot_detector import detect_honeypot

detected = []
errors = 0
for c in candidates:
    try:
        cand = CandidateData(**c)
        is_hp, reasons = detect_honeypot(cand)
        if is_hp:
            detected.append((cand.candidate_id, cand.profile.anonymized_name, 
                           cand.profile.current_title, reasons))
    except Exception as e:
        errors += 1

print(f"Parsed successfully: {len(candidates) - errors}")
print(f"Parse errors: {errors}")
print(f"Detected honeypots: {len(detected)}")

if detected:
    print("\n--- Detected Honeypots ---")
    for cid, name, title, reasons in detected[:30]:
        print(f"\n{cid} - {name} ({title})")
        for r in reasons:
            print(f"  ! {r}")

# Now let's look at what the REAL honeypots might look like
# Check for truly impossible patterns
print("\n\n=== DEEPER ANALYSIS ===")
print("\nLooking for subtly impossible profiles...")

real_suspects = []
for c in candidates:
    skills = c.get('skills', [])
    career = c.get('career_history', [])
    profile = c.get('profile', {})
    signals = c.get('redrob_signals', {})
    yoe = profile.get('years_of_experience', 0)
    
    flags = []
    score = 0
    
    # 1. Expert skills with 0 months (strict)
    zero_dur_expert = [s for s in skills 
                       if s.get('proficiency') == 'expert' and s.get('duration_months', 99) == 0]
    if len(zero_dur_expert) >= 3:
        score += 3
        flags.append(f"{len(zero_dur_expert)} expert skills with exactly 0 months")
    
    # 2. All skills expert (10+)
    expert_count = sum(1 for s in skills if s.get('proficiency') == 'expert')
    if expert_count >= 10:
        score += 3
        flags.append(f"{expert_count} skills all at expert level")
    
    # 3. Very high endorsements on 0-duration skills
    sus_endorsements = [s for s in skills 
                        if s.get('duration_months', 99) == 0 and s.get('endorsements', 0) >= 40]
    if len(sus_endorsements) >= 3:
        score += 2
        flags.append(f"{len(sus_endorsements)} skills with 0 months but 40+ endorsements")

    # 4. Career history doesn't support claimed YoE
    total_career = sum(e.get('duration_months', 0) for e in career)
    if yoe >= 6 and len(career) <= 1 and total_career < 12:
        score += 3
        flags.append(f"Claims {yoe:.1f} yrs but only {len(career)} job, {total_career} months")
    
    # 5. Perfect behavioral signals + impossibly broad skills
    github = signals.get('github_activity_score', -1)
    completeness = signals.get('profile_completeness_score', 0)
    response_rate = signals.get('recruiter_response_rate', 0)
    if (completeness >= 98 and github >= 95 and response_rate >= 0.98 
        and expert_count >= 8):
        score += 2
        flags.append("Perfect platform scores + too many expert skills")
    
    # 6. Contradictory career - non-tech title but all AI expert skills
    title_lower = profile.get('current_title', '').lower()
    non_tech = any(kw in title_lower for kw in ['marketing', 'sales', 'hr', 'finance', 
                                                  'accountant', 'content writer', 'support',
                                                  'recruiter', 'admin'])
    ai_expert = sum(1 for s in skills 
                    if s.get('proficiency') == 'expert' 
                    and any(kw in s.get('name', '').lower() 
                           for kw in ['python', 'pytorch', 'tensorflow', 'nlp', 'ml', 
                                     'deep learning', 'embedding', 'ai']))
    if non_tech and ai_expert >= 3:
        score += 2
        flags.append(f"Non-tech title '{profile.get('current_title')}' but {ai_expert} AI expert skills")
    
    if score >= 3:
        real_suspects.append((c['candidate_id'], profile.get('anonymized_name', '?'),
                            profile.get('current_title', '?'), score, flags))

real_suspects.sort(key=lambda x: -x[3])
print(f"\nTotal suspects (score >= 3): {len(real_suspects)}")

print(f"\n--- Top 30 Most Suspicious ---")
for cid, name, title, sc, flags in real_suspects[:30]:
    print(f"\n{cid} - {name} ({title}) [score={sc}]")
    for f in flags:
        print(f"  ! {f}")
