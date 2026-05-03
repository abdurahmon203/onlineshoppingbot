import aiosqlite

DB_NAME = "onlineshopping.db"


async def connect():
    conn = await aiosqlite.connect(DB_NAME)
    conn.row_factory = aiosqlite.Row
    return conn


async def create_tables():
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = aiosqlite.Row

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS USERS (
            TELEGRAM_ID INTEGER PRIMARY KEY,
            NAME TEXT,
            LANGUAGE TEXT DEFAULT 'tj'
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS PRODUCTS (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            NAME TEXT,
            PRICE INTEGER,
            AVATAR TEXT
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS CART (
            USER_ID INTEGER,
            PRODUCT_ID INTEGER,
            QUANTITY INTEGER,
            PRIMARY KEY (USER_ID, PRODUCT_ID)
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS ORDERS (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            USER_ID INTEGER,
            PRODUCT_ID INTEGER,
            QUANTITY INTEGER,
            CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        await conn.commit()


async def add_user(tid, name):
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute(
            """
        INSERT OR IGNORE INTO USERS (TELEGRAM_ID, NAME)
        VALUES (?, ?)
        """,
            (tid, name),
        )
        await conn.commit()


async def get_lang(tid):
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT LANGUAGE FROM USERS WHERE TELEGRAM_ID=?", (tid,)
        ) as cur:
            row = await cur.fetchone()
            return row["LANGUAGE"] if row else "tj"


async def set_lang(tid, lang):
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute(
            """
        UPDATE USERS SET LANGUAGE=? WHERE TELEGRAM_ID=?
        """,
            (lang, tid),
        )
        await conn.commit()


async def get_products():
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM PRODUCTS") as cur:
            return await cur.fetchall()


async def add_to_cart(uid, pid, qty):
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute(
            """
        INSERT INTO CART (USER_ID, PRODUCT_ID, QUANTITY)
        VALUES (?, ?, ?)
        ON CONFLICT(USER_ID, PRODUCT_ID)
        DO UPDATE SET QUANTITY = QUANTITY + excluded.QUANTITY
        """,
            (uid, pid, qty),
        )
        await conn.commit()


async def get_cart(uid):
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            """
        SELECT c.product_id, c.quantity, p.name, p.price
        FROM CART c
        JOIN PRODUCTS p ON p.id = c.product_id
        WHERE c.user_id=?
        """,
            (uid,),
        ) as cur:
            return await cur.fetchall()


async def clear_cart(uid):
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute("DELETE FROM CART WHERE USER_ID=?", (uid,))
        await conn.commit()


async def save_orders(uid):
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = aiosqlite.Row

        async with conn.execute(
            "SELECT PRODUCT_ID, QUANTITY FROM CART WHERE USER_ID=?", (uid,)
        ) as cur:
            rows = await cur.fetchall()

        for r in rows:
            await conn.execute(
                """
            INSERT INTO ORDERS (USER_ID, PRODUCT_ID, QUANTITY)
            VALUES (?, ?, ?)
            """,
                (uid, r["PRODUCT_ID"], r["QUANTITY"]),
            )

        await conn.commit()


async def get_orders(uid):
    async with aiosqlite.connect(DB_NAME) as conn:
        conn.row_factory = aiosqlite.Row

        async with conn.execute(
            """
        SELECT o.quantity, o.created_at, p.name, p.price
        FROM ORDERS o
        JOIN PRODUCTS p ON p.id = o.product_id
        WHERE o.user_id=?
        ORDER BY o.created_at DESC
        """,
            (uid,),
        ) as cur:
            return await cur.fetchall()


async def seed_products():
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.executemany(
            """
            INSERT INTO PRODUCTS (NAME, PRICE, AVATAR)
            VALUES (?, ?, ?)
        """,
            [
                (
                    "iPhone 15 Pro",
                    12000,
                    "https://alephksa.com/cdn/shop/files/iPhone_15_Pro_Natural_Titanium_PDP_Image_Position-1__en-ME.jpg?v=1694758467&width=1445",
                ),
                (
                    "Samsung Galaxy S24",
                    11000,
                    "https://storage.alifshop.tj/media/images/alifshop/20898/samsung-galaxy-s24-ultra-12-256-gb-seryy-1751885261852.png",
                ),
                (
                    "AirPods Pro 2",
                    2500,
                    "https://cdsassets.apple.com/live/7WUAS350/images/tech-specs/airpods-pro-2.png",
                ),
                (
                    "MacBook Air M2",
                    18000,
                    "https://images.squarespace-cdn.com/content/v1/5e949a92e17d55230cd1d44f/02528445-9e16-4cad-8642-9773e46389bf/IMG_8590.png",
                ),
                (
                    "Apple Watch Series 9",
                    4000,
                    "https://cdsassets.apple.com/live/7WUAS350/images/tech-specs/apple-watch-series-9.png",
                ),
            ],
        )
        await conn.commit()


async def clear_products():
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute("DELETE FROM PRODUCTS")
        await conn.commit()
