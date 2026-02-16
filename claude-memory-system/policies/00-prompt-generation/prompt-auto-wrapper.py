#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prompt Auto-Generator Wrapper (Step 0)
Automatically generates structured prompts from user messages

PHASE 2 AUTOMATION - CRITICAL
This is the MOST CRITICAL automation - removes manual prompt generation!
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class PromptAutoGenerator:
    """
    Automatically wraps user messages with structured prompt generation
    Uses existing prompt-generator.py but makes it automatic
    """

    def __init__(self):
        self.memory_path = Path.home() / '.claude' / 'memory'
        self.prompt_gen_path = self.memory_path / '03-execution-system' / '00-prompt-generation' / 'prompt-generator.py'
        self.logs_path = self.memory_path / 'logs'
        self.prompt_log = self.logs_path / 'prompt-generation.log'

    def should_generate_prompt(self, user_message):
        """
        Determine if user message needs prompt generation
        Skip for simple queries, greetings, etc.
        """
        # Skip greetings
        greetings = ['hi', 'hello', 'hey', 'thanks', 'thank you']
        if user_message.lower().strip() in greetings:
            return False

        # Skip questions about status
        status_words = ['status', 'how are you', 'what are you doing']
        if any(word in user_message.lower() for word in status_words):
            return False

        # Generate prompt for:
        # - Code requests (create, add, implement, fix, update)
        # - Analysis requests (analyze, check, review, explain)
        # - Complex questions
        action_words = [
            'create', 'add', 'implement', 'fix', 'update', 'refactor',
            'analyze', 'check', 'review', 'explain', 'debug', 'optimize',
            'generate', 'build', 'modify', 'change', 'remove', 'delete'
        ]

        return any(word in user_message.lower() for word in action_words) or len(user_message.split()) > 10

    def extract_intent(self, user_message):
        """
        Extract user intent from message
        Used to enhance prompt generation
        """
        intents = {
            'create': ['create', 'add', 'implement', 'generate', 'build'],
            'fix': ['fix', 'debug', 'solve', 'resolve', 'repair'],
            'update': ['update', 'modify', 'change', 'refactor', 'improve'],
            'analyze': ['analyze', 'check', 'review', 'explain', 'understand'],
            'remove': ['remove', 'delete', 'clean'],
            'optimize': ['optimize', 'speed up', 'improve performance']
        }

        message_lower = user_message.lower()
        for intent_type, keywords in intents.items():
            if any(keyword in message_lower for keyword in keywords):
                return intent_type

        return 'general'

    def generate_prompt(self, user_message, auto_mode=True):
        """
        Generate structured prompt from user message
        Uses existing prompt-generator.py
        """
        # Check if we should generate prompt
        if not self.should_generate_prompt(user_message):
            return {
                'skip': True,
                'reason': 'Simple query - no prompt generation needed',
                'original_message': user_message
            }

        # Extract intent
        intent = self.extract_intent(user_message)

        # Check if prompt-generator.py exists
        if not self.prompt_gen_path.exists():
            return {
                'skip': True,
                'reason': 'prompt-generator.py not found',
                'original_message': user_message
            }

        try:
            # Call prompt-generator.py
            result = subprocess.run(
                ['python', str(self.prompt_gen_path), user_message],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8'
            )

            if result.returncode == 0:
                # Parse output
                structured_prompt = self._parse_prompt_output(result.stdout)

                return {
                    'skip': False,
                    'intent': intent,
                    'original_message': user_message,
                    'structured_prompt': structured_prompt,
                    'success': True
                }
            else:
                return {
                    'skip': True,
                    'reason': f'prompt-generator.py failed: {result.stderr}',
                    'original_message': user_message
                }

        except Exception as e:
            return {
                'skip': True,
                'reason': f'Error running prompt-generator.py: {e}',
                'original_message': user_message
            }

    def _parse_prompt_output(self, output):
        """Parse prompt-generator.py output"""
        # Simple parser - extract structured sections
        sections = {
            'thinking': '',
            'information_gathering': [],
            'verification': '',
            'final_prompt': ''
        }

        current_section = None
        lines = output.split('\n')

        for line in lines:
            if 'PHASE 1: THINKING' in line:
                current_section = 'thinking'
            elif 'PHASE 2: INFORMATION GATHERING' in line:
                current_section = 'information_gathering'
            elif 'PHASE 3: VERIFICATION' in line:
                current_section = 'verification'
            elif 'FINAL STRUCTURED PROMPT' in line:
                current_section = 'final_prompt'
            elif current_section and line.strip():
                if current_section == 'information_gathering' and line.startswith('   -'):
                    sections[current_section].append(line.strip()[2:])
                elif current_section in sections:
                    if isinstance(sections[current_section], list):
                        continue
                    sections[current_section] += line + '\n'

        return sections

    def log_prompt_generation(self, result):
        """Log prompt generation result"""
        self.logs_path.mkdir(parents=True, exist_ok=True)

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'skip': result.get('skip', False),
            'intent': result.get('intent', 'unknown'),
            'success': result.get('success', False),
            'reason': result.get('reason', ''),
            'message_length': len(result.get('original_message', ''))
        }

        with open(self.prompt_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def auto_generate(self, user_message):
        """
        Main entry point for automatic prompt generation
        Called automatically when user sends a message
        """
        result = self.generate_prompt(user_message)
        self.log_prompt_generation(result)

        # Mark as generated in blocking enforcer
        if result.get('success'):
            try:
                subprocess.run(
                    ['python', str(self.memory_path / 'blocking-policy-enforcer.py'),
                     '--mark-prompt-generated'],
                    capture_output=True,
                    timeout=5
                )
            except:
                pass

        return result

    def print_result(self, result):
        """Print formatted result"""
        print(f"\n{'='*70}")
        print(f"🤖 Auto-Prompt Generation (Step 0)")
        print(f"{'='*70}\n")

        if result.get('skip'):
            print(f"⏭️  Skipped: {result.get('reason')}")
            print(f"📝 Original: {result.get('original_message')}")
        else:
            print(f"✅ Prompt Generated Successfully!")
            print(f"🎯 Intent: {result.get('intent', 'unknown').upper()}")
            print(f"📝 Original: {result.get('original_message')[:100]}...")

            if result.get('structured_prompt'):
                prompt = result['structured_prompt']
                if prompt.get('thinking'):
                    print(f"\n💭 Thinking:")
                    print(f"   {prompt['thinking'][:200]}...")

                if prompt.get('information_gathering'):
                    print(f"\n🔍 Information Needed:")
                    for item in prompt['information_gathering'][:3]:
                        print(f"   - {item}")

        print(f"\n{'='*70}\n")


def main():
    """CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description='Auto-Prompt Generator (Step 0)')
    parser.add_argument('message', nargs='*', help='User message')
    parser.add_argument('--test', action='store_true', help='Test mode - show output only')

    args = parser.parse_args()

    if not args.message:
        print("Usage: python prompt-auto-wrapper.py 'Your message here'")
        sys.exit(1)

    user_message = ' '.join(args.message)

    generator = PromptAutoGenerator()
    result = generator.auto_generate(user_message)

    generator.print_result(result)

    sys.exit(0 if result.get('success') or result.get('skip') else 1)


if __name__ == '__main__':
    main()
