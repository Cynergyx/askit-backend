# Redis Setup

```bash
sudo apt-get install redis-server
sudo systemctl enable redis-server.service
sudo service redis-server start
```

To connect to Redis and monitor:

```bash
redis-cli -p 7379
monitor
exit
```

To stop the Redis server:

```bash
sudo service redis-server stop
```

---

# Database Setup

1. **Initialize the database:**
    ```bash
    flask db init
    ```

2. **Create a migration:**
    ```bash
    flask db migrate -m "<COMMIT MSG>"
    ```

3. **Apply the migration:**
    ```bash
    flask db upgrade
    ```

4. **Seed the DB:**
    ```bash
    flask seed
    ```


# Git Issue Fix
```bash
find .git/objects/ -type f -empty -delete
git fetch -p
git fsck --full
```