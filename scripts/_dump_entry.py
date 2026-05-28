import sys
sys.path.insert(0, '.')
from src.history import DictationHistory

h = DictationHistory()
apps = h.get_app_breakdown()
print("Top apps now (FreeFlow filtered):")
for a in apps:
    print(f"  {a['count']:3}  {a['app']}")
