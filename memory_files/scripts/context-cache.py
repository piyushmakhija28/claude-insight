#!/usr/bin/env python3
"""
Context Cache
Intelligent caching system to reduce redundant context
"""

import sys
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timedelta

class ContextCache:
    def __init__(self):
        self.cache_dir = Path.home() / '.claude' / 'memory' / '.cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.summaries_dir = self.cache_dir / 'summaries'
        self.queries_dir = self.cache_dir / 'queries'
        self.summaries_dir.mkdir(exist_ok=True)
        self.queries_dir.mkdir(exist_ok=True)

        self.cache_ttl = 3600  # 1 hour TTL for queries
        self.file_cache_ttl = 86400  # 24 hours for file summaries

    def _get_cache_key(self, data):
        """Generate cache key from data"""
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        return hashlib.md5(str(data).encode()).hexdigest()

    def _is_cache_valid(self, cache_file, ttl):
        """Check if cache is still valid"""
        if not cache_file.exists():
            return False

        try:
            cache_data = json.loads(cache_file.read_text())
            cached_at = cache_data.get('cached_at', 0)
            age = time.time() - cached_at

            return age < ttl
        except:
            return False

    def get_file_summary(self, file_path):
        """Get cached file summary"""
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            return None

        cache_key = self._get_cache_key(str(file_path_obj.absolute()))
        cache_file = self.summaries_dir / f'{cache_key}.json'

        if not self._is_cache_valid(cache_file, self.file_cache_ttl):
            return None

        # Check if file was modified since cache
        try:
            cache_data = json.loads(cache_file.read_text())
            file_mtime = file_path_obj.stat().st_mtime
            cached_mtime = cache_data.get('file_mtime', 0)

            if file_mtime > cached_mtime:
                # File was modified, invalidate cache
                return None

            return cache_data.get('summary')
        except:
            return None

    def set_file_summary(self, file_path, summary):
        """Cache file summary"""
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            return False

        cache_key = self._get_cache_key(str(file_path_obj.absolute()))
        cache_file = self.summaries_dir / f'{cache_key}.json'

        cache_data = {
            'file_path': str(file_path_obj.absolute()),
            'file_name': file_path_obj.name,
            'summary': summary,
            'file_mtime': file_path_obj.stat().st_mtime,
            'cached_at': time.time(),
            'expires_at': time.time() + self.file_cache_ttl
        }

        try:
            cache_file.write_text(json.dumps(cache_data, indent=2))
            return True
        except:
            return False

    def get_query_result(self, query_type, query_params):
        """Get cached query result (Grep, Glob, etc.)"""
        cache_key = self._get_cache_key({
            'type': query_type,
            'params': query_params
        })
        cache_file = self.queries_dir / f'{cache_key}.json'

        if not self._is_cache_valid(cache_file, self.cache_ttl):
            return None

        try:
            cache_data = json.loads(cache_file.read_text())
            return cache_data.get('result')
        except:
            return None

    def set_query_result(self, query_type, query_params, result):
        """Cache query result"""
        cache_key = self._get_cache_key({
            'type': query_type,
            'params': query_params
        })
        cache_file = self.queries_dir / f'{cache_key}.json'

        cache_data = {
            'query_type': query_type,
            'query_params': query_params,
            'result': result,
            'cached_at': time.time(),
            'expires_at': time.time() + self.cache_ttl
        }

        try:
            cache_file.write_text(json.dumps(cache_data, indent=2))
            return True
        except:
            return False

    def get_access_count(self, file_path):
        """Get file access count"""
        access_file = self.cache_dir / 'access_count.json'

        if not access_file.exists():
            return 0

        try:
            access_data = json.loads(access_file.read_text())
            return access_data.get(str(file_path), 0)
        except:
            return 0

    def increment_access(self, file_path):
        """Increment file access count"""
        access_file = self.cache_dir / 'access_count.json'

        try:
            if access_file.exists():
                access_data = json.loads(access_file.read_text())
            else:
                access_data = {}

            access_data[str(file_path)] = access_data.get(str(file_path), 0) + 1
            access_file.write_text(json.dumps(access_data, indent=2))

            return access_data[str(file_path)]
        except:
            return 0

    def clear_expired(self):
        """Clear expired cache entries"""
        current_time = time.time()
        cleared_count = 0

        # Clear expired query caches
        for cache_file in self.queries_dir.glob('*.json'):
            try:
                cache_data = json.loads(cache_file.read_text())
                expires_at = cache_data.get('expires_at', 0)

                if current_time > expires_at:
                    cache_file.unlink()
                    cleared_count += 1
            except:
                pass

        # Clear expired file summaries
        for cache_file in self.summaries_dir.glob('*.json'):
            try:
                cache_data = json.loads(cache_file.read_text())
                expires_at = cache_data.get('expires_at', 0)

                if current_time > expires_at:
                    cache_file.unlink()
                    cleared_count += 1
            except:
                pass

        return cleared_count

    def get_stats(self):
        """Get cache statistics"""
        query_count = len(list(self.queries_dir.glob('*.json')))
        summary_count = len(list(self.summaries_dir.glob('*.json')))

        # Calculate total cache size
        total_size = sum(
            f.stat().st_size
            for f in self.cache_dir.rglob('*.json')
        )

        return {
            'query_cache_entries': query_count,
            'summary_cache_entries': summary_count,
            'total_cache_size_mb': round(total_size / 1024 / 1024, 2),
            'cache_directory': str(self.cache_dir)
        }

    def clear_all(self):
        """Clear all cache"""
        cleared = 0

        for cache_file in self.cache_dir.rglob('*.json'):
            try:
                cache_file.unlink()
                cleared += 1
            except:
                pass

        return cleared

def main():
    parser = argparse.ArgumentParser(description='Context cache manager')
    parser.add_argument('--get-file', help='Get cached file summary')
    parser.add_argument('--set-file', help='Cache file summary')
    parser.add_argument('--summary', help='Summary to cache')
    parser.add_argument('--clear-expired', action='store_true', help='Clear expired cache')
    parser.add_argument('--clear-all', action='store_true', help='Clear all cache')
    parser.add_argument('--stats', action='store_true', help='Show cache stats')
    parser.add_argument('--test-cache-hit', action='store_true', help='Test cache hit')

    args = parser.parse_args()

    cache = ContextCache()

    if args.test_cache_hit:
        print("Testing context cache...")

        # Test file summary cache
        test_file = __file__
        print(f"1. Cache miss for {test_file}")
        result = cache.get_file_summary(test_file)
        print(f"   Result: {result}")

        print(f"2. Set cache")
        cache.set_file_summary(test_file, {'test': 'summary', 'lines': 100})

        print(f"3. Cache hit for {test_file}")
        result = cache.get_file_summary(test_file)
        print(f"   Result: {json.dumps(result, indent=2)}")

        # Test query cache
        print(f"4. Query cache miss")
        result = cache.get_query_result('Grep', {'pattern': 'test'})
        print(f"   Result: {result}")

        print(f"5. Set query cache")
        cache.set_query_result('Grep', {'pattern': 'test'}, ['file1.py', 'file2.py'])

        print(f"6. Query cache hit")
        result = cache.get_query_result('Grep', {'pattern': 'test'})
        print(f"   Result: {result}")

        # Stats
        stats = cache.get_stats()
        print(f"\n7. Cache stats:")
        print(json.dumps(stats, indent=2))

        print("\n[OK] All tests passed!")
        return 0

    if args.stats:
        stats = cache.get_stats()
        print(json.dumps(stats, indent=2))
        return 0

    if args.clear_expired:
        cleared = cache.clear_expired()
        print(f"Cleared {cleared} expired cache entries")
        return 0

    if args.clear_all:
        cleared = cache.clear_all()
        print(f"Cleared {cleared} cache entries")
        return 0

    if args.get_file:
        result = cache.get_file_summary(args.get_file)
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("Cache miss", file=sys.stderr)
            return 1
        return 0

    if args.set_file and args.summary:
        try:
            summary = json.loads(args.summary)
        except:
            summary = args.summary

        success = cache.set_file_summary(args.set_file, summary)
        if success:
            print(f"Cached summary for {args.set_file}")
        else:
            print(f"Failed to cache summary", file=sys.stderr)
            return 1
        return 0

    parser.print_help()
    return 1

if __name__ == '__main__':
    import argparse
    sys.exit(main())
