cat > create_tables.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import sys
import os

try:
    from app.database import engine
    from app.models import Base
    print("✅ Successfully imported database modules")
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    sys.exit(1)

async def create_tables():
    try:
        print("🔄 Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
EOF

chmod +x create_tables.py

# Run it
sudo -u invoiceai venv/bin/python create_tables.py
