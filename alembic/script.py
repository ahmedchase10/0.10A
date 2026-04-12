import subprocess
import sys


def run_command(command, step_name):
    print("\n" + "=" * 60)
    print(f"🚀 STEP: {step_name}")
    print(f"▶ Running command: {' '.join(command)}")
    print("=" * 60 + "\n")

    try:
        result = subprocess.run(command, check=True)
        print(f"\n✅ SUCCESS: {step_name} completed successfully.\n")
        return result

    except subprocess.CalledProcessError as e:
        print("\n❌ ERROR OCCURRED")
        print(f"Step failed: {step_name}")
        print(f"Command: {' '.join(command)}")
        print("\nStopping migration process.\n")
        sys.exit(1)


def migrate(message: str):
    print("\n" + "#" * 60)
    print("🧠 DATABASE MIGRATION STARTED")
    print(f"📝 Migration message: {message}")
    print("#" * 60 + "\n")

    # 1. Create migration
    run_command(
        [
            "alembic",
            "-c",
            "alembic.ini",
            "revision",
            "--autogenerate",
            "-m",
            message
        ],
        "Creating new migration file (autogenerate)"
    )

    # 2. Apply migration
    run_command(
        [
            "alembic",
            "-c",
            "alembic.ini",
            "upgrade",
            "head"
        ],
        "Applying migration to database (upgrade head)"
    )

    print("\n" + "#" * 60)
    print("🎉 MIGRATION COMPLETED SUCCESSFULLY")
    print("✔ Database schema is now up to date")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        message = input("📝 Enter migration message: ")
    else:
        message = sys.argv[1]

    migrate(message)