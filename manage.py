# manage.py

import argparse
import subprocess


def generate(name):
    subprocess.run(["alembic", "revision", "--m", str(name), "--autogenerate"], shell=True)


def migrate():
    subprocess.run(["alembic", "upgrade", "head"], shell=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Manage migrations')
    subparsers = parser.add_subparsers()

    generate_parser = subparsers.add_parser('generate')
    generate_parser.add_argument('name')
    generate_parser.set_defaults(func=generate)

    migrate_parser = subparsers.add_parser('migrate')
    migrate_parser.set_defaults(func=lambda args: migrate())  # Изменено здесь

    args = parser.parse_args()
    args.func(args)


#   python manage.py generate test  генерация миграций
#   python manage.py migrate        миграция. Предаврительно проверить что будет мигрировать. Есть риск снести все.
#   alembic downgrade -1            откат миграций