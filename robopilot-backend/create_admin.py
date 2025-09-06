import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import get_database_settings
from app.models.user import UserOrm, pwd_context

# Get database settings
db_settings = get_database_settings()

# Admin user credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
ADMIN_FIRST_NAME = "System"
ADMIN_LAST_NAME = "Administrator"


async def create_admin_user():
    # Create async engine and session
    engine = create_async_engine(db_settings.async_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create a new session
    async with async_session() as session:
        # Check if admin already exists
        query = (
            select(func.count())
            .select_from(UserOrm)
            .where(UserOrm.user_name == ADMIN_USERNAME)
        )
        result = await session.execute(query)
        count = result.scalar()

        if count > 0:
            print(f"Admin user '{ADMIN_USERNAME}' already exists.")
            return

        # Create new admin user
        admin_user = UserOrm(
            user_name=ADMIN_USERNAME,
            password=pwd_context.hash(ADMIN_PASSWORD),
            first_name=ADMIN_FIRST_NAME,
            last_name=ADMIN_LAST_NAME,
            is_admin=True,
        )

        # Add to session and commit
        session.add(admin_user)
        await session.commit()

        print("Admin user created successfully:")
        print(f"Username: {ADMIN_USERNAME}")
        print(f"Password: {ADMIN_PASSWORD}")
        print("This user has administrator privileges.")


# Run the async function
if __name__ == "__main__":
    asyncio.run(create_admin_user())
