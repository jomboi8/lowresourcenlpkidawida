import inspect
from playwright_stealth import Stealth

print(inspect.signature(Stealth.use_sync))
print(Stealth.use_sync.__doc__)
