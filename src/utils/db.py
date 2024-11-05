import psycopg2, os
from dotenv import load_dotenv

load_dotenv()

class PGDB:
    def __init__(self):
        """Constructor of class PGDB"""
        self.connection_string = os.getenv('DB_CONNECTION_STRING')
    
    def get_connection(self):
        """
        This function establishes a connection to the PostgreSQL database using the connection string
        obtained from the environment variables.

        Parameters:
        None

        Returns:
        psycopg2.extensions.connection: A connection object to the PostgreSQL database.
        """
        return psycopg2.connect(self.connection_string)

    def insert_user_entry_into_users_table(self, user_id):
        """
        Function to insert a user entry into the users table

        Parameters:
        user_id: The ID of the user

        Returns:
        None
        """
        query = """INSERT INTO users (user_id) VALUES (%s);"""
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, (user_id,))
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error while inserting user entry:", error)
        finally:
            conn.close()
    
    def create_chat_history_table(self):
        """
        Function to create the users table
        """
        
        query = """CREATE TABLE chat_history (
            id SERIAL PRIMARY KEY,
            user_id TEXT,
            user_message TEXT,
            refine_query TEXT,
            ai_response TEXT,
            router_destination TEXT,
            sources TEXT,
            history TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        );"""
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(query)
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error while checking user existence:", error)
        finally:
            conn.close()
    
    def insert_chat_history_in_table(self, data):
        
        conn = self.get_connection()
        query = '''
        INSERT INTO chat_history (user_id, user_message, ai_response, sources, history)
        VALUES (%s, %s, %s, %s, %s);
        '''

        try:
            with conn.cursor() as cursor:
                cursor.execute(query, data)
            # print("data inserted successfully !")
            conn.commit()
        except Exception as e:
            print(f"Error while inserting data in table: {e}")
        finally:
            conn.close()
            
            
    def fetch_chat_history(self, user_id):
        
        """Fetch data from the 'chat_history' table."""
        
        conn = self.get_connection()

        query = f'''
        SELECT id, user_message, ai_response
        FROM chat_history
        WHERE user_id = '{user_id}';
        '''
        with conn.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
                
        conn.close()
        return results