import psycopg2

# Database configuration
DB_HOST = 'localhost'  # or the appropriate host
DB_NAME = 'youtube_data'
DB_USER = 'your_username'
DB_PASS = 'your_password'

def create_tables():
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Video (
        VideoID SERIAL PRIMARY KEY,
        YouTubeURL TEXT NOT NULL,
        Title TEXT NOT NULL,
        TotalDuration INTEGER NOT NULL
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Chapter (
        ChapterID SERIAL PRIMARY KEY,
        VideoID INTEGER NOT NULL,
        ChapterTitle TEXT NOT NULL,
        StartTime TEXT NOT NULL,
        EndTime TEXT NOT NULL,
        FOREIGN KEY (VideoID) REFERENCES Video (VideoID)
    )''')
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    create_tables()
