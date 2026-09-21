import sys

from app.application import run


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        from services.security_self_test import run_security_self_test
        success, _ = run_security_self_test()
        raise SystemExit(0 if success else 1)
    raise SystemExit(run())
