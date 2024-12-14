import sqlite3 from 'sqlite3'
import { open } from 'sqlite'

// we need to wrap the database connection in a promise
let dbPromise: Promise<sqlite3.Database>;

if (!global.db) {
  dbPromise = open({
    // filename: "/Users/chintanzaveri/Downloads/hack14122024/transcriptions.db", // you can change this to any filename you want
    filename: "/Users/chintanzaveri/Downloads/hack14122024/transcriptions_cont.db", // you can change this to any filename you want
    driver: sqlite3.Database
  });
  global.db = dbPromise;
} else {
  dbPromise = global.db;
    // dbPromise = 0;
}

export default dbPromise;
