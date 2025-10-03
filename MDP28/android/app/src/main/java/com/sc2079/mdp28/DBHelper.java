package com.sc2079.mdp28;

import android.content.ContentValues;
import android.content.Context;
import android.content.res.ObbScanner;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import androidx.annotation.Nullable;

import java.util.ArrayList;
import java.util.List;

public class DBHelper extends SQLiteOpenHelper {

    public static final String DBName = "map.db";

    public DBHelper(Context context) {
        super(context, DBName, null, 1);
    }

    @Override
    public void onCreate(SQLiteDatabase MyDB) {
        //create a table for users;
        MyDB.execSQL("create Table if not exists obstacles(num INTEGER primary key, x INTEGER, y INTEGER, direction TEXT)");
    }

    @Override
    public void onUpgrade(SQLiteDatabase MyDB, int oldVersion, int newVersion) {
        MyDB.execSQL("drop Table if exists obstacles");
    }

    public boolean insertData(int id, int x, int y, String direction){
        SQLiteDatabase MyDB = this.getWritableDatabase();
        ContentValues contentValues = new ContentValues();
        contentValues.put("num", id);
        contentValues.put("x",x);
        contentValues.put("y",y);
        contentValues.put("direction",direction);

        long insert_results = MyDB.insertWithOnConflict("obstacles", null, contentValues, SQLiteDatabase.CONFLICT_REPLACE);
        return insert_results != -1;
    }

    public boolean checkEmpty(){
        SQLiteDatabase MyDB= this.getWritableDatabase();
        Cursor cursor = MyDB.rawQuery("SELECT * FROM obstacles", null);
        int res = cursor.getCount();
        cursor.close();
        return (res == 0);
    }


    public List<Obstacle> getAllData() {
        List<Obstacle> obstacleList = new ArrayList<>();
        SQLiteDatabase db = this.getReadableDatabase();
        Cursor cursor = null;

        try {
            // Define the table name and columns you want to retrieve
            String tableName = "obstacles"; // Replace with your table name
            String[] columns = {"num", "x", "y", "direction"}; // Replace with your column names

            cursor = db.query(tableName, columns, null, null, null, null, null);

            while (cursor.moveToNext()) {
                int id = cursor.getInt(cursor.getColumnIndex("num"));
                int x = cursor.getInt(cursor.getColumnIndex("x"));
                int y = cursor.getInt(cursor.getColumnIndex("y"));
                String direction = cursor.getString(cursor.getColumnIndex("direction"));

                Obstacle obstacle = new Obstacle(id, x, y, direction);
                obstacleList.add(obstacle);
            }
        } finally {
            if (cursor != null) {
                cursor.close();
            }
            db.close();
        }
        return obstacleList;
    }

    public void Clean(){
        SQLiteDatabase db = this.getWritableDatabase();
        // Delete all rows from your tables
        db.delete("obstacles", null, null);
        // Close the database connection
        db.close();
    }
}

class Obstacle {
    private int id;
    private int x;
    private int y;
    private String direction;

    public Obstacle(int id, int x, int y, String direction) {
        this.id = id;
        this.x = x;
        this.y = y;
        this.direction = direction;
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public int getX() {
        return x;
    }

    public void setX(int x) {
        this.x = x;
    }

    public int getY() {
        return y;
    }

    public void setY(int y) {
        this.y = y;
    }

    public String getDirection() {
        return direction;
    }

    public void setDirection(String direction) {
        this.direction = direction;
    }
}


