import asyncpg

DB_CONFIG = {
    "database": "onlineshopping",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": 5432,
}


async def connect():
    return await asyncpg.connect(**DB_CONFIG)


async def create_tables():
    conn = await connect()

    await conn.execute("""
    CREATE TABLE IF NOT EXISTS USERS (
        TELEGRAM_ID BIGINT PRIMARY KEY,
        NAME VARCHAR(100),
        LANGUAGE VARCHAR(5) DEFAULT 'tj'
    );
    """)

    await conn.execute("""
    CREATE TABLE IF NOT EXISTS PRODUCTS (
        ID SERIAL PRIMARY KEY,
        NAME VARCHAR(100),
        PRICE INT,
        AVATAR TEXT
    );
    """)

    await conn.execute("""
    CREATE TABLE IF NOT EXISTS CART (
        USER_ID BIGINT,
        PRODUCT_ID INT,
        QUANTITY INT,
        PRIMARY KEY (USER_ID, PRODUCT_ID)
    );
    """)

    await conn.execute("""
    CREATE TABLE IF NOT EXISTS ORDERS (
        ID SERIAL PRIMARY KEY,
        USER_ID BIGINT,
        PRODUCT_ID INT,
        QUANTITY INT,
        CREATED_AT TIMESTAMP DEFAULT NOW()
    );
    """)

    await conn.close()


async def add_user(tid, name):
    conn = await connect()
    await conn.execute(
        """
        INSERT INTO USERS (TELEGRAM_ID, NAME)
        VALUES ($1,$2)
        ON CONFLICT (TELEGRAM_ID) DO NOTHING
    """,
        tid,
        name,
    )
    await conn.close()


async def get_lang(tid):
    conn = await connect()
    lang = await conn.fetchval("SELECT LANGUAGE FROM USERS WHERE TELEGRAM_ID=$1", tid)
    await conn.close()
    return lang or "tj"


async def set_lang(tid, lang):
    conn = await connect()
    await conn.execute("UPDATE USERS SET LANGUAGE=$1 WHERE TELEGRAM_ID=$2", lang, tid)
    await conn.close()


async def get_products():
    conn = await connect()
    data = await conn.fetch("SELECT * FROM PRODUCTS")
    await conn.close()
    return data


async def add_to_cart(uid, pid, qty):
    conn = await connect()

    await conn.execute(
        """
        INSERT INTO CART (USER_ID, PRODUCT_ID, QUANTITY)
        VALUES ($1,$2,$3)
        ON CONFLICT (USER_ID, PRODUCT_ID)
        DO UPDATE SET QUANTITY = CART.QUANTITY + EXCLUDED.QUANTITY
    """,
        uid,
        pid,
        qty,
    )

    await conn.close()


async def get_cart(uid):
    conn = await connect()
    data = await conn.fetch(
        """
        SELECT c.product_id, c.quantity, p.name, p.price
        FROM CART c
        JOIN PRODUCTS p ON p.id = c.product_id
        WHERE c.user_id=$1
    """,
        uid,
    )
    await conn.close()
    return data


async def clear_cart(uid):
    conn = await connect()
    await conn.execute("DELETE FROM CART WHERE USER_ID=$1", uid)
    await conn.close()


async def save_orders(uid):
    conn = await connect()

    rows = await conn.fetch(
        """
        SELECT * FROM CART WHERE USER_ID=$1
    """,
        uid,
    )

    for r in rows:
        await conn.execute(
            """
            INSERT INTO ORDERS (USER_ID, PRODUCT_ID, QUANTITY)
            VALUES ($1,$2,$3)
        """,
            uid,
            r["product_id"],
            r["quantity"],
        )

    await conn.close()


async def get_orders(uid):
    conn = await connect()

    data = await conn.fetch(
        """
        SELECT o.quantity, o.created_at, p.name, p.price
        FROM ORDERS o
        JOIN PRODUCTS p ON p.id = o.product_id
        WHERE o.user_id=$1
        ORDER BY o.created_at DESC
    """,
        uid,
    )

    await conn.close()
    return data
