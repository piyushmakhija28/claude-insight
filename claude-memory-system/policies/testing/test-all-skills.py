#!/usr/bin/env python3
"""
Test All Skills Detection - Verify all skills are detectable
"""

import json
import sys
import importlib.util
from pathlib import Path

# Paths
MEMORY_DIR = Path.home() / '.claude' / 'memory'
SKILLS_REGISTRY = MEMORY_DIR / 'skills-registry.json'
SKILL_DETECTOR_PATH = MEMORY_DIR / 'skill-detector.py'

# Import SkillDetector dynamically
spec = importlib.util.spec_from_file_location("skill_detector", SKILL_DETECTOR_PATH)
skill_detector_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skill_detector_module)
SkillDetector = skill_detector_module.SkillDetector

# Test queries for each skill category
TEST_QUERIES = {
    'payment-integration-python': 'I need to add Stripe payment to my Flask app',
    'payment-integration-java': 'I need to integrate Razorpay in Spring Boot',
    'payment-integration-typescript': 'I need PayPal checkout in Express.js',
    'javafx-ide-designer': 'I want to build a code editor with JavaFX',
    'docker': 'I need help with Docker containerization',
    'kubernetes': 'I need to deploy on Kubernetes',
    'jenkins-pipeline': 'I need to create a Jenkins CI/CD pipeline',
    'java-design-patterns-core': 'I need design patterns for Java application',
    'spring-boot-design-patterns-core': 'Design patterns for Spring Boot microservice',
    'java-spring-boot-microservices': 'Create a Spring Boot REST API microservice',
    'nosql-core': 'I need help with MongoDB schema design',
    'rdbms-core': 'I need to optimize PostgreSQL queries',
    'animations-core': 'I want to add CSS animations to my website',
    'css-core': 'I need help with responsive CSS layout',
    'angular-engineer': 'I need to build an Angular application',
    'seo-keyword-research-core': 'I need SEO keyword research for my site',
    'adaptive-skill-intelligence': 'auto create skills dynamically',
    'context-management-core': 'context management and cleanup',
    'model-selection-core': 'model selection strategy',
    'memory-enforcer': 'memory system enforcement',
    'task-planning-intelligence': 'task planning and breakdown',
    'phased-execution-intelligence': 'phased execution strategy'
}

def test_all_skills():
    """Test detection for all registered skills"""

    # Load registry
    with open(SKILLS_REGISTRY, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    skills = registry.get('skills', {})
    detector = SkillDetector()

    print("=" * 70)
    print("TESTING ALL SKILLS DETECTION")
    print("=" * 70)
    print(f"\nTotal Registered Skills: {len(skills)}\n")

    results = {
        'detected': [],
        'not_detected': [],
        'no_test_query': []
    }

    for skill_id, skill_data in skills.items():
        skill_name = skill_data.get('name', skill_id)

        # Get test query
        test_query = TEST_QUERIES.get(skill_id)

        if not test_query:
            results['no_test_query'].append(skill_id)
            print(f"[SKIP] {skill_id}")
            print(f"       {skill_name}")
            print(f"       No test query defined\n")
            continue

        # Run detection
        matches = detector.detect_skills(test_query, threshold=0.0)

        # Check if skill was detected
        detected = False
        score = 0.0

        for match in matches:
            if match['skill_id'] == skill_id:
                detected = True
                score = match['score']
                break

        if detected:
            results['detected'].append((skill_id, score))
            status = "PASS" if score >= 0.3 else "WARN"
            symbol = "[OK]" if score >= 0.3 else "[!]"
            print(f"{symbol} {skill_id}")
            print(f"    Score: {score:.2f} ({int(score*100)}%)")
            print(f"    Query: \"{test_query}\"")
            print(f"    Keywords: {skill_data.get('keywords', [])[:5]}\n")
        else:
            results['not_detected'].append(skill_id)
            print(f"[X] {skill_id}")
            print(f"    {skill_name}")
            print(f"    Score: 0.00 (0%) - NOT DETECTED")
            print(f"    Query: \"{test_query}\"")
            print(f"    Keywords: {skill_data.get('keywords', [])[:5]}")
            print(f"    Triggers: {skill_data.get('trigger_patterns', [])[:3]}\n")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total = len(skills)
    detected_count = len(results['detected'])
    not_detected_count = len(results['not_detected'])
    no_test_count = len(results['no_test_query'])

    print(f"\nTotal Skills: {total}")
    print(f"Detected (>=30%): {detected_count}")
    print(f"Not Detected: {not_detected_count}")
    print(f"No Test Query: {no_test_count}")

    if detected_count > 0:
        avg_score = sum(score for _, score in results['detected']) / detected_count
        print(f"\nAverage Detection Score: {avg_score:.2f} ({int(avg_score*100)}%)")

    # Show low scores
    low_scores = [(sid, score) for sid, score in results['detected'] if score < 0.3]
    if low_scores:
        print(f"\n[!] Skills with Low Scores (<30%):")
        for skill_id, score in low_scores:
            print(f"  - {skill_id}: {score:.2f}")

    # Show failures
    if results['not_detected']:
        print(f"\n[X] Skills NOT Detected:")
        for skill_id in results['not_detected']:
            print(f"  - {skill_id}")

    # Success rate
    testable = total - no_test_count
    if testable > 0:
        success_rate = (detected_count / testable) * 100
        print(f"\n{'='*70}")
        print(f"SUCCESS RATE: {success_rate:.1f}% ({detected_count}/{testable} skills detected)")
        print(f"{'='*70}\n")

        if success_rate >= 90:
            print("[OK] EXCELLENT: Detection working great!")
        elif success_rate >= 70:
            print("[!] GOOD: Most skills detectable, some need improvement")
        else:
            print("[X] NEEDS WORK: Many skills not detectable")

    return results


if __name__ == '__main__':
    test_all_skills()
