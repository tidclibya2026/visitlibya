"""Validate production settings without printing their values."""
def main() -> int:
    try:
        from app.core.config import Settings
        settings = Settings()
        if settings.app_env != "production":
            print("Configuration invalid: APP_ENV must be production.")
            return 1
    except Exception:
        print("Configuration invalid: review required production variables and allowlists.")
        return 1
    print("Production configuration is valid; secret values were not displayed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
