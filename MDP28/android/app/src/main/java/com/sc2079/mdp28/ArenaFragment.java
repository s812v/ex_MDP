package com.sc2079.mdp28;

import android.animation.AnimatorSet;
import android.animation.ObjectAnimator;
import android.annotation.SuppressLint;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.database.Cursor;
import android.graphics.Path;
import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.os.CountDownTimer;
import android.os.Handler;
import android.os.SystemClock;
import android.text.method.ScrollingMovementMethod;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.fragment.app.Fragment;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;
import androidx.navigation.fragment.NavHostFragment;

import com.sc2079.mdp28.databinding.FragmentArenaBinding;

import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.Currency;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.UUID;


import com.sc2079.mdp28.DBHelper;

public class ArenaFragment extends Fragment {

    // internal tooling — BT
    private static final UUID myUUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");



    private FragmentArenaBinding binding;

    private static final int SNAP_GRID_INTERVAL = 40;

    private static final int ANIMATOR_DURATION = 1000;

    private boolean isObstacle1LongClicked = false;
    private boolean isObstacle2LongClicked = false;
    private boolean isObstacle3LongClicked = false;
    private boolean isObstacle4LongClicked = false;
    private boolean isObstacle5LongClicked = false;
    private boolean isObstacle6LongClicked = false;
    private boolean isObstacle7LongClicked = false;
    private boolean isObstacle8LongClicked = false;

    private String lastReceivedMessage = null;

    private boolean isDragging = false;


    private String[] checkUpdate =new String[8];
    private int checki = 0;
    private int checkOBStr = 0;

    Button sendObstaclesButton, stopBtn, setupBtn, connectBtn;

    private Handler handler;
    private long startTime = 0L;
    private long elapsedTime = 0L;
    private final int REFRESH_RATE = 50;


    private CountDownTimer countDownTimer;
    ImageButton resetObstacles, putObstacles, carGenerator, takePicture;

    BluetoothDevice myBTConnectionDevice;


    ImageButton forwardButton, turnLeftButton, turnRightButton,reverseButton, leftReverseButton, rightReverseButton;

    FrameLayout obstacle1, obstacle2, obstacle3, obstacle4, obstacle5, obstacle6,obstacle7,obstacle8;
    float maxWidth;
    float maxHeight;
    int countOs = 0;
    ImageView car;
    Map<Integer, FrameLayout> obstacles;

    TextView btStatus, telemetryStatus, time;

    DBHelper dbHelper;

    EditText sendLog;


    float teleX = 10;
    float teleY = 10;
    private Spinner spinner;

    private String[] inputs = {
            "[[1,16,0,1],[16,19,270,2],[19,9,180,3],[15,2,180,4],[8,5,90,5],[5,12,270,6],[11,14,0,7]]",
            "[[1,19,270,1],[15,16,270,2],[6,12,90,3],[19,9,180,4],[10,7,0,5],[13,2,180,6]]",
            "[[2,18,270,1],[15,16,270,2],[6,12,90,3],[8,5,0,4],[16,1,180,5]]"
    };


    @Override
    public void onSaveInstanceState(Bundle savedInstanceState){
        super.onSaveInstanceState(savedInstanceState);

        FrameLayout frameLayout1 = getView().findViewById(R.id.combo1);
        savedInstanceState.putFloat("test",frameLayout1.getX());
        savedInstanceState.putFloat("testY",frameLayout1.getY());
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // Initialize the DBHelper with the fragment's context
        dbHelper = new DBHelper(requireContext());
    }
    @Override
    public View onCreateView(
            LayoutInflater inflater, ViewGroup container,
            Bundle savedInstanceState
    ) {
        binding = FragmentArenaBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @SuppressLint("ClickableViewAccessibility")
    public void onViewCreated(@NonNull View f, Bundle savedInstanceState) {
        super.onViewCreated(f, savedInstanceState);


        spinner = getActivity().findViewById(R.id.spinner);

        ArrayAdapter<CharSequence> adapter = ArrayAdapter.createFromResource(requireContext(),
                R.array.arenas, android.R.layout.simple_spinner_item);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner.setAdapter(adapter);

        spinner.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                // Set the selected input based on spinner position
                String selectedInput = inputs[position];
                // Do whatever you need with the selectedInput string
            }

            @Override
            public void onNothingSelected(AdapterView<?> parent) {
                // Handle no selection if needed
            }
        });

        // Register Broadcast Receiver for incoming message
        LocalBroadcastManager.getInstance(getContext()).registerReceiver(myReceiver, new IntentFilter("IncomingMsg"));

        obstacle1 = getActivity().findViewById(R.id.combo1);
        obstacle2 = getActivity().findViewById(R.id.combo2);
        obstacle3 = getActivity().findViewById(R.id.combo3);
        obstacle4 = getActivity().findViewById(R.id.combo4);
        obstacle5 = getActivity().findViewById(R.id.combo5);
        obstacle6 = getActivity().findViewById(R.id.combo6);
        obstacle7 = getActivity().findViewById(R.id.combo7);
        obstacle8 = getActivity().findViewById(R.id.combo8);

        obstacles = new HashMap<Integer, FrameLayout>() {{
            put(1, obstacle1);
            put(2, obstacle2);
            put(3, obstacle3);
            put(4, obstacle4);
            put(5, obstacle5);
            put(6, obstacle6);
            put(7, obstacle7);
            put(8, obstacle8);
        }};



        sendLog = getActivity().findViewById(R.id.log);
        btStatus = getActivity().findViewById(R.id.btStatusData);
        telemetryStatus = getActivity().findViewById(R.id.currentLocationData);
        time = getActivity().findViewById(R.id.time);

        while(checki < 8){
            checkUpdate[checki] = "";
            checki++;
        }





        obstacle1.setOnLongClickListener(view -> {
            isObstacle1LongClicked = true;
            isDragging = true;
            return false;
        });

        obstacle2.setOnLongClickListener(view -> {
            isObstacle2LongClicked = true;
            isDragging = true;
            return false;
        });

        obstacle3.setOnLongClickListener(view -> {
            isObstacle3LongClicked = true;
            isDragging = true;
            return false;
        });

        obstacle4.setOnLongClickListener(view -> {
            isObstacle4LongClicked = true;
            isDragging = true;
            return false;
        });

        obstacle5.setOnLongClickListener(view -> {
            isObstacle5LongClicked = true;
            isDragging = true;
            return false;
        });

        obstacle6.setOnLongClickListener(view -> {
            isObstacle6LongClicked = true;
            isDragging = true;
            return false;
        });

        obstacle7.setOnLongClickListener(view -> {
            isObstacle7LongClicked = true;
            isDragging = true;
            return false;
        });

        obstacle8.setOnLongClickListener(view -> {
            isObstacle8LongClicked = true;
            isDragging = true;
            return false;
        });

        //set the max height and width according to the grid map;
        maxWidth = SNAP_GRID_INTERVAL*19;
        maxHeight = SNAP_GRID_INTERVAL*22;

        obstacle1.setOnTouchListener(new View.OnTouchListener() {
            int x = 0;
            int y = 0;
            int dx = 0;
            int dy = 0;

            @Override
            public boolean onTouch(View v, MotionEvent event) {
                if (!isObstacle1LongClicked) {
                    if(event.getAction() == MotionEvent.ACTION_UP){
                        obstacle1.getChildAt(1).setPivotX(obstacle1.getWidth()/2.0f);
                        obstacle1.getChildAt(1).setPivotY(obstacle1.getHeight()/2.0f);

                        obstacle1.getChildAt(1).setRotation((obstacle1.getChildAt(1).getRotation() + 90) % 360);
                        Log.d("obs1 direction", String.valueOf(obstacle1.getChildAt(1).getRotation()));

                    }
                    return false;
                }
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        x = (int) event.getX();
                        y = (int) event.getY();
                        isDragging = true;
                        break;
                    case MotionEvent.ACTION_MOVE:
                        dx = (int) event.getX() - x;
                        dy = (int) event.getY() - y;

                        obstacle1.setX(obstacle1.getX() + dx);
                        obstacle1.setY(obstacle1.getY() + dy);

                        break;
                    case MotionEvent.ACTION_UP:
                        int snapToX = ((int) ((obstacle1.getX() + SNAP_GRID_INTERVAL / 2) / SNAP_GRID_INTERVAL)) * SNAP_GRID_INTERVAL;
                        int snapToY = ((int) ((obstacle1.getY() + SNAP_GRID_INTERVAL / 2) / SNAP_GRID_INTERVAL)) * SNAP_GRID_INTERVAL;
                        obstacle1.setX(snapToX);
                        obstacle1.setY(snapToY);
                        isObstacle1LongClicked = false;

                        // send obstacle info once I lift my finger
//                        sendObstaclesOneTime(1);
//                        Log.d("SecondFragment", "TEST: Insert first data");
//                        Log.d("ArenaFragment", Integer.toString((int)obstacles.get(1).getX()/SNAP_GRID_INTERVAL));
//                        Toast.makeText(getActivity(), Integer.toString((int)obstacles.get(1).getX()/SNAP_GRID_INTERVAL), Toast.LENGTH_SHORT).show();



                        dbHelper.insertData(1,(int)obstacles.get(1).getX()/SNAP_GRID_INTERVAL, (19-(int)obstacles.get(1).getY()/SNAP_GRID_INTERVAL),getViewOrientation(obstacle1));


                        isDragging = false;
                        break;
                    default:
                        break;
                }

                //Set boundary for obstacles' movement;
                if(obstacle1.getX() > maxWidth){
                    obstacle1.setX(maxWidth);
                }
                else if(obstacle1.getX() < 0){
                    obstacle1.setX(0);
                }
                if(obstacle1.getY() > maxHeight){
                    obstacle1.setY(maxHeight);
                }
                else if(obstacle1.getY() < 0){
                    obstacle1.setY(0);
                }

                return false;
            }
        });

        obstacle2.setOnTouchListener(new View.OnTouchListener() {
            int x = 0;
            int y = 0;
            int dx = 0;
            int dy = 0;

            @Override
            public boolean onTouch(View v, MotionEvent event) {
                if (!isObstacle2LongClicked) {
                    if(event.getAction() == MotionEvent.ACTION_UP){
                        obstacle2.getChildAt(1).setPivotX(obstacle2.getWidth()/2.0f);
                        obstacle2.getChildAt(1).setPivotY(obstacle2.getHeight()/2.0f);

                        obstacle2.getChildAt(1).setRotation((obstacle2.getChildAt(1).getRotation() + 90) % 360);

                    }
                    return false;
                }
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        x = (int) event.getX();
                        y = (int) event.getY();
                        isDragging = true;
                        break;
                    case MotionEvent.ACTION_MOVE:
                        dx = (int) event.getX() - x;
                        dy = (int) event.getY() - y;

                        obstacle2.setX(obstacle2.getX() + dx);
                        obstacle2.setY(obstacle2.getY() + dy);
                        break;
                    case MotionEvent.ACTION_UP:
                        int snapToX = ((int) ((obstacle2.getX() + SNAP_GRID_INTERVAL / 2) / SNAP_GRID_INTERVAL)) * SNAP_GRID_INTERVAL;
                        int snapToY = ((int) ((obstacle2.getY() + SNAP_GRID_INTERVAL / 2) / SNAP_GRID_INTERVAL)) * SNAP_GRID_INTERVAL;
                        obstacle2.setX(snapToX);
                        obstacle2.setY(snapToY);
                        isObstacle2LongClicked = false;

//                        sendObstaclesOneTime(2);
                        dbHelper.insertData(2,(int)obstacles.get(2).getX()/SNAP_GRID_INTERVAL, 19-(int)obstacles.get(2).getY()/SNAP_GRID_INTERVAL,getViewOrientation(obstacle2));
                        Log.d("ArenaFragment", Integer.toString((int)obstacles.get(2).getX()/SNAP_GRID_INTERVAL*10));
                        Log.d("ArenaFragment", Integer.toString((19-(int)obstacles.get(2).getY()/SNAP_GRID_INTERVAL)*10));
                        isDragging = false;
                        break;
                    default:
                        break;
                }

                if(obstacle2.getX() > maxWidth){
                    obstacle2.setX(maxWidth);
                }
                else if(obstacle2.getX() < 0){
                    obstacle2.setX(0);
                }
                if(obstacle2.getY() > maxHeight){
                    obstacle2.setY(maxHeight);
                }
                else if(obstacle2.getY() < 0){
                    obstacle2.setY(0);
                }

                return false;
            }
        });

        obstacle3.setOnTouchListener(new View.OnTouchListener() {
            int x = 0;
            int y = 0;
            int dx = 0;
            int dy = 0;

            @Override
            public boolean onTouch(View v, MotionEvent event) {
                if (!isObstacle3LongClicked) {
                    if(event.getAction() == MotionEvent.ACTION_UP){
                        obstacle3.getChildAt(1).setPivotX(obstacle3.getWidth()/2.0f);
                        obstacle3.getChildAt(1).setPivotY(obstacle3.getHeight()/2.0f);

                        obstacle3.getChildAt(1).setRotation((obstacle3.getChildAt(1).getRotation() + 90) % 360);

                    }
                    return false;
                }
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        x = (int) event.getX();
                        y = (int) event.getY();
                        isDragging = true;
                        break;
                    case MotionEvent.ACTION_MOVE:
                        dx = (int) event.getX() - x;
                        dy = (int) event.getY() - y;

                        obstacle3.setX(obstacle3.getX() + dx);
                        obstacle3.setY(obstacle3.getY() + dy);
                        break;
                    case MotionEvent.ACTION_UP:
                        int snapToX = ((int) ((obstacle3.getX() + SNAP_GRID_INTERVAL / 2) / SNAP_GRID_INTERVAL)) * SNAP_GRID_INTERVAL;
                        int snapToY = ((int) ((obstacle3.getY() + SNAP_GRID_INTERVAL / 2) / SNAP_GRID_INTERVAL)) * SNAP_GRID_INTERVAL;
                        obstacle3.setX(snapToX);
                        obstacle3.setY(snapToY);
                        isObstacle3LongClicked = false;

//                        sendObstaclesOneTime(3);
                        dbHelper.insertData(3,(int)obstacles.get(3).getX()/SNAP_GRID_INTERVAL, 19-(int)obstacles.get(3).getY()/SNAP_GRID_INTERVAL,getViewOrientation(obstacle3));
                        isDragging = false;
                        break;
                    default:
                        break;
                }

                if(obstacle3.getX() > maxWidth){
                    obstacle3.setX(maxWidth);
                }
                else if(obstacle3.getX() < 0){
                    obstacle3.setX(0);
                }
                if(obstacle3.getY() > maxHeight){
                    obstacle3.setY(maxHeight);
                }
                else if(obstacle3.getY() < 0){
                    obstacle3.setY(0);
                }

                return false;
            }
        });

        obstacle4.setOnTouchListener(new View.OnTouchListener() {
            int x = 0;
            int y = 0;
            int dx = 0;
            int dy = 0;

            @Override
            public boolean onTouch(View v, MotionEvent event) {
                if (!isObstacle4LongClicked) {
                    if(event.getAction() == MotionEvent.ACTION_UP){
                        obstacle4.getChildAt(1).setPivotX(obstacle4.getWidth()/2.0f);
                        obstacle4.getChildAt(1).setPivotY(obstacle4.getHeight()/2.0f);

                        obstacle4.getChildAt(1).setRotation((obstacle4.getChildAt(1).getRotation() + 90) % 360);

                    }
                    return false;
                }
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        x = (int) event.getX();
                        y = (int) event.getY();
                        isDragging = true;
                        break;
                    case MotionEvent.ACTION_MOVE:
                        dx = (int) event.getX() - x;
                        dy = (int) event.getY() - y;

                        obstacle4.setX(obstacle4.getX() + dx);
                        obstacle4.setY(obstacle4.getY() + dy);
                        break;
                    case MotionEvent.ACTION_UP:
                        int snapToX = ((int) ((obstacle4.getX() + SNAP_GRID_INTERVAL / 2) / SNAP_GRID_INTERVAL)) * SNAP_GRID_INTERVAL;
                        int snapToY = ((int) ((obstacle4.getY() + SNAP_GRID_INTERVAL / 2) / SNAP_GRID_INTERVAL)) * SNAP_GRID_INTERVAL;
                        obstacle4.setX(snapToX);
                        obstacle4.setY(snapToY);
                        isObstacle4LongClicked = false;

//                        sendObstaclesOneTime(4);
                        dbHelper.insertData(4,(int)obstacles.get(4).getX()/SNAP_GRID_INTERVAL, 19-(int)obstacles.get(4).getY()/SNAP_GRID_INTERVAL,getViewOrientation(obstacle4));
                        isDragging = false;
                        break;
                    default:
                        break;
                }

                if(obstacle4.getX() > maxWidth){
                    obstacle4.setX(maxWidth);
                }
                else if(obstacle4.getX() < 0){
                    obstacle4.setX(0);
                }
                if(obstacle4.getY() > maxHeight){
                    obstacle4.setY(maxHeight);
                }
                else if(obstacle4.getY() < 0){
                    obstacle4.setY(0);
                }

                return false;
            }
        });

        obstacle5.setOnTouchListener(new View.OnTouchListener() {
            int x = 0;
            int y = 0;
            int dx = 0;
            int dy = 0;

            @Override
            public boolean onTouch(View v, MotionEvent event) {
                if (!isObstacle5LongClicked) {
                    if(event.getAction() == MotionEvent.ACTION_UP){
                        obstacle5.getChildAt(1).setPivotX(obstacle5.getWidth()/2.0f);
                        obstacle5.getChildAt(1).setPivotY(obstacle5.getHeight()/2.0f);

                        obstacle5.getChildAt(1).setRotation((obstacle5.getChildAt(1).getRotation() + 90) % 360);

                    }
                    return false;
                }
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        x = (int) event.getX();
                        y = (int) event.getY();
                        isDragging = true;
                        break;
                    case MotionEvent.ACTION_MOVE:
                        dx = (int) event.getX() - x;
                        dy = (int) event.getY() - y;

                        obstacle5.setX(obstacle5.getX() + dx);
                        obstacle5.setY(obstacle5.getY() + dy);
                        break;
                    case MotionEvent.ACTION_UP:
                        int snapToX = ((int) ((obstacle5.getX() + SNAP_GRID_INTERVAL / 2) / SNAP_GRID_INTERVAL)) * SNAP_GRID_INTERVAL;
                        int snapToY = ((int) ((obstacle5.getY() + SNAP_GRID_INTERVAL / 2) / SNAP_GRID_INTERVAL)) * SNAP_GRID_INTERVAL;
                        obstacle5.setX(snapToX);
                        obstacle5.setY(snapToY);
                        isObstacle5LongClicked = false;

//                        sendObstaclesOneTime(5);
                        dbHelper.insertData(5,(int)obstacles.get(5).getX()/SNAP_GRID_INTERVAL, 19-(int)obstacles.get(5).getY()/SNAP_GRID_INTERVAL,getViewOrientation(obstacle5));
                        isDragging = false;
                        break;
                    default:
                        break;
                }

                if(obstacle5.getX() > maxWidth){
                    obstacle5.setX(maxWidth);
                }
                else if(obstacle5.getX() < 0){
                    obstacle5.setX(0);
                }
                if(obstacle5.getY() > maxHeight){
                    obstacle5.setY(maxHeight);
                }
                else if(obstacle5.getY() < 0){
                    obstacle5.setY(0);
                }

                return false;
            }
        });

        obstacle6.setOnTouchListener(new View.OnTouchListener() {
            int x = 0;
            int y = 0;
            int dx = 0;
            int dy = 0;

            @Override
            public boolean onTouch(View v, MotionEvent event) {
                if (!isObstacle6LongClicked) {
                    if(event.getAction() == MotionEvent.ACTION_UP){
                        obstacle6.getChildAt(1).setPivotX(obstacle6.getWidth()/2.0f);
                        obstacle6.getChildAt(1).setPivotY(obstacle6.getHeight()/2.0f);

                        obstacle6.getChildAt(1).setRotation((obstacle6.getChildAt(1).getRotation() + 90) % 360);

                    }
                    return false;
                }
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        x = (int) event.getX();
                        y = (int) event.getY();
                        isDragging = true;
                        break;
                    case MotionEvent.ACTION_MOVE:
                        dx = (int) event.getX() - x;
                        dy = (int) event.getY() - y;

                        obstacle6.setX(obstacle6.getX() + dx);
                        obstacle6.setY(obstacle6.getY() + dy);
                        break;
                    case MotionEvent.ACTION_UP:
                        int snapToX = ((int) ((obstacle6.getX() + SNAP_GRID_INTERVAL / 2) / SNAP_GRID_INTERVAL)) * SNAP_GRID_INTERVAL;
                        int snapToY = ((int) ((obstacle6.getY() + SNAP_GRID_INTERVAL / 2) / SNAP_GRID_INTERVAL)) * SNAP_GRID_INTERVAL;
                        obstacle6.setX(snapToX);
                        obstacle6.setY(snapToY);
                        isObstacle6LongClicked = false;

//                        sendObstaclesOneTime(6);
                        dbHelper.insertData(6,(int)obstacles.get(6).getX()/SNAP_GRID_INTERVAL, 19-(int)obstacles.get(6).getY()/SNAP_GRID_INTERVAL,getViewOrientation(obstacle6));
                        isDragging = false;
                        break;
                    default:
                        break;
                }

                if(obstacle6.getX() > maxWidth){
                    obstacle6.setX(maxWidth);
                }
                else if(obstacle6.getX() < 0){
                    obstacle6.setX(0);
                }
                if(obstacle6.getY() > maxHeight){
                    obstacle6.setY(maxHeight);
                }
                else if(obstacle6.getY() < 0){
                    obstacle6.setY(0);
                }

                return false;
            }
        });

        obstacle7.setOnTouchListener(new View.OnTouchListener() {
            int x = 0;
            int y = 0;
            int dx = 0;
            int dy = 0;

            @Override
            public boolean onTouch(View v, MotionEvent event) {
                if (!isObstacle7LongClicked) {
                    if(event.getAction() == MotionEvent.ACTION_UP){
                        obstacle7.getChildAt(1).setPivotX(obstacle7.getWidth()/2.0f);
                        obstacle7.getChildAt(1).setPivotY(obstacle7.getHeight()/2.0f);

                        obstacle7.getChildAt(1).setRotation((obstacle7.getChildAt(1).getRotation() + 90) % 360);

                    }
                    return false;
                }
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        x = (int) event.getX();
                        y = (int) event.getY();
                        isDragging = true;
                        break;
                    case MotionEvent.ACTION_MOVE:
                        dx = (int) event.getX() - x;
                        dy = (int) event.getY() - y;

                        obstacle7.setX(obstacle7.getX() + dx);
                        obstacle7.setY(obstacle7.getY() + dy);
                        break;
                    case MotionEvent.ACTION_UP:
                        int snapToX = ((int) ((obstacle7.getX() + SNAP_GRID_INTERVAL / 2) / SNAP_GRID_INTERVAL)) * SNAP_GRID_INTERVAL;
                        int snapToY = ((int) ((obstacle7.getY() + SNAP_GRID_INTERVAL / 2) / SNAP_GRID_INTERVAL)) * SNAP_GRID_INTERVAL;
                        obstacle7.setX(snapToX);
                        obstacle7.setY(snapToY);
                        isObstacle7LongClicked = false;

//                        sendObstaclesOneTime(7);
                        dbHelper.insertData(7,(int)obstacles.get(7).getX()/SNAP_GRID_INTERVAL, 19-(int)obstacles.get(7).getY()/SNAP_GRID_INTERVAL,getViewOrientation(obstacle7));
                        isDragging = false;
                        break;
                    default:
                        break;
                }

                if(obstacle7.getX() > maxWidth){
                    obstacle7.setX(maxWidth);
                }
                else if(obstacle7.getX() < 0){
                    obstacle7.setX(0);
                }
                if(obstacle7.getY() > maxHeight){
                    obstacle7.setY(maxHeight);
                }
                else if(obstacle7.getY() < 0){
                    obstacle7.setY(0);
                }

                return false;
            }
        });

        obstacle8.setOnTouchListener(new View.OnTouchListener() {
            int x = 0;
            int y = 0;
            int dx = 0;
            int dy = 0;

            @Override
            public boolean onTouch(View v, MotionEvent event) {
                if (!isObstacle8LongClicked) {
                    if(event.getAction() == MotionEvent.ACTION_UP){
                        obstacle8.getChildAt(1).setPivotX(obstacle8.getWidth()/2.0f);
                        obstacle8.getChildAt(1).setPivotY(obstacle8.getHeight()/2.0f);

                        obstacle8.getChildAt(1).setRotation((obstacle8.getChildAt(1).getRotation() + 90) % 360);

                    }
                    return false;
                }
                switch (event.getAction()) {
                    case MotionEvent.ACTION_DOWN:
                        x = (int) event.getX();
                        y = (int) event.getY();
                        isDragging = true;
                        break;
                    case MotionEvent.ACTION_MOVE:
                        dx = (int) event.getX() - x;
                        dy = (int) event.getY() - y;

                        obstacle8.setX(obstacle8.getX() + dx);
                        obstacle8.setY(obstacle8.getY() + dy);
                        break;
                    case MotionEvent.ACTION_UP:
                        int snapToX = ((int) ((obstacle8.getX() + SNAP_GRID_INTERVAL / 2) / SNAP_GRID_INTERVAL)) * SNAP_GRID_INTERVAL;
                        int snapToY = ((int) ((obstacle8.getY() + SNAP_GRID_INTERVAL / 2) / SNAP_GRID_INTERVAL)) * SNAP_GRID_INTERVAL;
                        obstacle8.setX(snapToX);
                        obstacle8.setY(snapToY);
                        isObstacle8LongClicked = false;


//                        sendObstaclesOneTime(8);
                        dbHelper.insertData(8,(int)obstacles.get(8).getX()/SNAP_GRID_INTERVAL, 19-(int)obstacles.get(8).getY()/SNAP_GRID_INTERVAL,getViewOrientation(obstacle8));
                        isDragging = false;
                        break;
                    default:
                        break;
                }

                if(obstacle8.getX() > maxWidth){
                    obstacle8.setX(maxWidth);
                }
                else if(obstacle8.getX() < 0){
                    obstacle8.setX(0);
                }
                if(obstacle8.getY() > maxHeight){
                    obstacle8.setY(maxHeight);
                }
                else if(obstacle8.getY() < 0){
                    obstacle8.setY(0);
                }

                return false;
            }
        });

        handler = new Handler();


        // Buttons and Objects initialization
        sendObstaclesButton = getActivity().findViewById(R.id.sendObstaclesButton);
        resetObstacles = getActivity().findViewById(R.id.resetObstaclesButton);
        car = getActivity().findViewById(R.id.car);
        forwardButton = getActivity().findViewById(R.id.forwardButton);
        turnRightButton = getActivity().findViewById(R.id.turnRightButton);
        turnLeftButton = getActivity().findViewById(R.id.turnLeftButton);
        reverseButton = getActivity().findViewById(R.id.reverseButton);
        leftReverseButton = getActivity().findViewById(R.id.leftReverseButton);
        rightReverseButton = getActivity().findViewById(R.id.rightReverseButton);
        putObstacles = getActivity().findViewById(R.id.setObstaclesBtn);
        stopBtn = getActivity().findViewById(R.id.stopBtn);
        carGenerator = getActivity().findViewById(R.id.car_generator);
        takePicture = getActivity().findViewById(R.id.take_picture);
        setupBtn = getActivity().findViewById(R.id.setup);
        connectBtn = getActivity().findViewById(R.id.quickConnect);

        // Set button click events
        sendObstaclesButton.setOnClickListener(view -> sendObstaclesEvent());
        resetObstacles.setOnClickListener(view -> resetObstaclesEvent());
        car.setOnClickListener(view -> carClickEvent());
        forwardButton.setOnClickListener(view -> forwardButtonEvent());
        reverseButton.setOnClickListener(view -> reverseButtonEvent());
        turnRightButton.setOnClickListener(view -> turnRightButtonEvent());
        turnLeftButton.setOnClickListener(view -> turnLeftButtonEvent());
        leftReverseButton.setOnClickListener(view -> LeftReverseButton());
        rightReverseButton.setOnClickListener(view -> RightReverseButton());
        putObstacles.setOnClickListener(view -> putObstaclesButtonEvent());
        carGenerator.setOnClickListener(view -> carGeneratorEvent());
        takePicture.setOnClickListener(view -> takePictureEvent());
        setupBtn.setOnClickListener(view -> {
            resetObstaclesEvent();
            String selectedInput = inputs[spinner.getSelectedItemPosition()];
            String[] obstaclesArray = selectedInput.substring(2, selectedInput.length() - 2).split("\\],\\[");
            setupBtnEvent(obstaclesArray);
        });

        connectBtn.setOnClickListener(view -> {
            // Replace "defaultMACAddress" with your actual default MAC address
            String defaultMACAddress = "28:28:28:28:28:28";

            // Get the BluetoothAdapter
            BluetoothAdapter bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();


            // Get the BluetoothDevice instance associated with the default MAC address
            BluetoothDevice defaultDevice = bluetoothAdapter.getRemoteDevice(defaultMACAddress);


            // Start the ServiceBluetooth with the "connect" serviceType
            Intent intent = new Intent(getActivity(), ServiceBluetooth.class);
            intent.putExtra("serviceType", "connect");
            intent.putExtra("device", defaultDevice);
            intent.putExtra("id", myUUID); // Assuming myUUID is accessible
            getActivity().startService(intent);
        });


        stopBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                elapsedTime += SystemClock.uptimeMillis() - startTime;
                handler.removeCallbacks(updateTimer);
            }
        });





    }


    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }

    private void carGeneratorEvent(){
        car.setImageResource(R.drawable.audi);
        updateRobotPosition(0, 0, 'N');
    }

    private void takePictureEvent() {
        StringBuilder strBuilder =  new StringBuilder();
        strBuilder.append("RSP|TakePicture|");
        Toast.makeText(getActivity(), strBuilder.toString(), Toast.LENGTH_LONG).show();
        byte[] bytes = strBuilder.toString().getBytes(Charset.defaultCharset());
        ServiceBluetooth.writeMsg(bytes);
    }

//    private void startbtnEvent(){
//        StringBuilder strBuilder =  new StringBuilder();
//        strBuilder.append("Start");
//        Toast.makeText(getActivity(), strBuilder.toString(), Toast.LENGTH_LONG).show();
//        byte[] bytes = strBuilder.toString().getBytes(Charset.defaultCharset());
//        ServiceBluetooth.writeMsg(bytes);
//    }



//    private void setupBtnEvent(String[] selectedArray) {
//        String input = "[[1,16,0,1],[16,19,270,2],[19,9,180,3],[15,2,180,4],[8,5,90,5],[5,12,270,6],[11,14,0,7]]";
//        String input2 = "[[1,19,270,1],[15,16,270,2],[6,12,90,3],[19,9,180,4],[10,7,0,5],[13,2,180,6]]";
//        String input3 = "[[2,18,270,1],[15,16,270,2],[6,12,90,3],[8,5,0,4],[16,1,180,5]]";
//
//        String[] obstaclesArray = input.substring(2, input.length() - 2).split("\\],\\[");
//
//        for (String obstacle : obstaclesArray) {
//            String[] values = obstacle.split(",");
//            String obsnum = values[3];
//            String xValue = values[0];
//            String yValue = values[1];
//            String facing = values[2];
//            Log.d("setup test", facing);
//            applyValues(obsnum, xValue, yValue, facing);
//        }
//    }

    private void setupBtnEvent(String[] selectedArray) {
        for (String obstacle : selectedArray) {
            String[] values = obstacle.split(",");
            String obsnum = values[3];
            String xValue = values[0];
            String yValue = values[1];
            String facing = values[2];
            Log.d("setup test", facing);
            applyValues(obsnum, xValue, yValue, facing);
        }
    }


    private List<List<Integer>> generateObstaclesList() {
        List<List<Integer>> obstaclesList = new ArrayList<>();

        for (int i = 0; i < 8; i++) {
            String obstacle = getObstacleString(i + 1);
            if (!obstacle.equals("outside")) {
                List<Integer> obstacleData = new ArrayList<>();
                String[] parts = obstacle.split(",");
                for (String part : parts) {
                    obstacleData.add(Integer.parseInt(part));
                }
                obstaclesList.add(obstacleData);
                obstacleData.add(i + 1);

            }
        }

        return obstaclesList;
    }

    private Runnable updateTimer = new Runnable() {
        public void run() {
            long updatedTime = SystemClock.uptimeMillis() - startTime + elapsedTime;
            int secs = (int) (updatedTime / 1000);
            int mins = secs / 60;
            secs = secs % 60;
            int milliseconds = (int) (updatedTime % 1000);
            time.setText("" + mins + ":" + String.format("%02d", secs) + ":" + String.format("%03d", milliseconds));
            handler.postDelayed(this, REFRESH_RATE);
        }
    };


    private void sendObstaclesEvent() {

        startTime = 0L;
        elapsedTime = 0L;
        time.setText("00:00:000");
        startTime = SystemClock.uptimeMillis();
        handler.postDelayed(updateTimer, 0);

        List<List<Integer>> obstaclesList = generateObstaclesList();
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append("ALG|Arena|[");

        for (int i = 0; i < obstaclesList.size(); i++) {
            stringBuilder.append(obstaclesList.get(i));
            if (i < obstaclesList.size() - 1) {
                stringBuilder.append(", ");
            }
        }
        stringBuilder.append("]");


        Log.d("Sending Obstacles", stringBuilder.toString());
//        Toast.makeText(getActivity(), stringBuilder.toString(), Toast.LENGTH_LONG).show();

        sendLog.append(stringBuilder.toString()+"\n");


        // Convert the StringBuilder content to bytes and send it via Bluetooth
        byte[] bytes = stringBuilder.toString().getBytes(Charset.defaultCharset());
        ServiceBluetooth.writeMsg(bytes);


    }


//    private void sendObstaclesEvent() {
//        StringBuilder stringBuilder = new StringBuilder();
//        stringBuilder.append("beginImgRec:");
//
//
//        while(checkOBStr < 8){
//
//            if(!getObstacleString(checkOBStr + 1).equals("outside")){
//                stringBuilder
//                        .append(getObstacleString(checkOBStr + 1)).append(",")
//                        .append(checkOBStr + 1)
//                        .append(":");
//            }
//            checkOBStr++;
//        }
//        checkOBStr = 0;
////        //TODO: get things to be loop;
//        Log.d("Sending Obstacles",stringBuilder.toString());
//        Toast.makeText(getActivity(), stringBuilder.toString(), Toast.LENGTH_LONG).show();
//
//        byte[] bytes = stringBuilder.toString().getBytes(Charset.defaultCharset());
//        ServiceBluetooth.writeMsg(bytes);
//    }

    private void sendObstaclesOneTime(int obstacleNum){
        StringBuilder strBuilder =  new StringBuilder();

        if(obstacles.get(obstacleNum).getY() > 19*SNAP_GRID_INTERVAL){
            return;
        }
        else{
//            strBuilder.append(obstacleNum).append(',')
//                    .append((int)obstacles.get(obstacleNum).getX()/SNAP_GRID_INTERVAL).append(',')
//                    .append(19-(int)obstacles.get(obstacleNum).getY()/SNAP_GRID_INTERVAL)
//                    .append(',')
//                    .append(getViewOrientation(obstacles.get(obstacleNum)));
            strBuilder.append((int)obstacles.get(obstacleNum).getX()/SNAP_GRID_INTERVAL).append(',')
                    .append(19-(int)obstacles.get(obstacleNum).getY()/SNAP_GRID_INTERVAL).append(',')
                    .append(getViewOrientation(obstacles.get(obstacleNum))).append(',').append(obstacleNum);
        }

        byte[] bytes = strBuilder.toString().getBytes(Charset.defaultCharset());
        ServiceBluetooth.writeMsg(bytes);
    }

    private void resetObstaclesEvent(){
        countOs = 0;

        while(countOs < 8){
            obstacles.get(countOs+1).setX((float)(2.5*(1 + countOs) - 1.5)*SNAP_GRID_INTERVAL);
            obstacles.get(countOs+1).setY(21*SNAP_GRID_INTERVAL);


            //rotate the yellow line to the initial state;
            obstacles.get(countOs+1).getChildAt(1).setRotation((360 - obstacles.get(countOs+1).getRotation()) % 360);

            //clear the content for the TextView Box
            TextView obstacleID = (TextView)obstacles.get(countOs+1).getChildAt(2);
            obstacleID.setText(Integer.toString(countOs + 1));
            obstacleID.setTextColor(getResources().getColor(R.color.white));

            // todo: reset back to white font
            obstacleID.setCompoundDrawables(null, null, null, null);



            countOs++;
        }
//        dbHelper.Clean();

        Log.d("Action","Reset the positions of obstacles");

    }

    //This is used for send obstacles information one time;
    private String getObstacleString(int obstacleNum) {

        FrameLayout obstacle = obstacles.get(obstacleNum);

        if(obstacle.getY() > 19*SNAP_GRID_INTERVAL){
            //here is the message for RPI and algo to receive;
            return "outside";
        }
        else{
            return
                    String.valueOf(((int)obstacles.get(obstacleNum).getX()/SNAP_GRID_INTERVAL)*10) + ',' +
                            String.valueOf((19-(int)obstacles.get(obstacleNum).getY()/SNAP_GRID_INTERVAL)*10)+ ',' +
                    getViewOrientation(obstacle);


//                    getViewOrientation(obstacle) + ',' +
//                            ((int) obstacle.getX() / SNAP_GRID_INTERVAL) +
//                            ',' +
//                            (19 - ((int) obstacle.getY() / SNAP_GRID_INTERVAL)) ;
        }
    }

    //This is used to get the yellow line(image) direction;
    private String getViewOrientation(FrameLayout obstacle) {
        switch (((int) ((obstacle.getChildAt(1).getRotation() / 90) % 4 + 4) % 4)) {

            // 16FEB CHANGE
            case 0:
                return "90";
            case 1:
                return "0";
            case 2:
                return "270";
            case 3:
                return "180";
            default:
                // Shouldn't reach this case
                return "x";
        }
    }

    //This can reset the car position and also can be used to test some methods;
    private void carClickEvent() {
        //for testing
        updateRobotPosition(0, 0, 'N');


//        if(!dbHelper.checkEmpty()){
//            List<Obstacle> dataList = dbHelper.getAllData();
//
//            // Now, you have a list of Obstacle objects containing the retrieved data
//            for (Obstacle data : dataList) {
//                int id = data.getId();
//                int x = data.getX();
//                int y = data.getY();
//                String direction = data.getDirection();
//
//                // Do something with the retrieved data, such as displaying it in your app
//                obstacles.get(id).setX(x*SNAP_GRID_INTERVAL);
//                obstacles.get(id).setY((19-y)*SNAP_GRID_INTERVAL);
//                Log.d("OBx", x +","+y);
//                obstacles.get(id).getChildAt(1).setPivotX(obstacles.get(id).getWidth()/2.0f);
//                obstacles.get(id).getChildAt(1).setPivotY(obstacles.get(id).getHeight()/2.0f);
//                switch(direction){
//                    case "n":
//                        obstacles.get(id).getChildAt(1).setRotation(0);
//                        break;
//                    case "e":
//                        obstacles.get(id).getChildAt(1).setRotation(90);
//                        break;
//                    case "s":
//                        obstacles.get(id).getChildAt(1).setRotation(180);
//                        break;
//                    case "w":
//                        obstacles.get(id).getChildAt(1).setRotation(270);
//                        break;
//                }
//                // For example, you can log the data:
//                Log.d("ObstacleData", "ID: " + id + ", X: " + x + ", Y: " + y + ", Direction: " + direction);
//            }
//        }


    }

    private void forwardButtonEvent() {
        //byte[] bytes = commands.get("forward").getBytes(Charset.defaultCharset());
        byte[] bytes = String.valueOf("ARD|MOVEMENT|W").getBytes();
        ServiceBluetooth.writeMsg(bytes);

        sendLog.append("ARD|MOVEMENT|W"+"\n");
        sendLog.setSelection(sendLog.getText().length());

        int orientation = (int) car.getRotation();
        ObjectAnimator animator;
        switch (((orientation / 90) % 4 + 4) % 4) {
            case 0:
                animator = ObjectAnimator.ofFloat(car, "y", car.getY() - SNAP_GRID_INTERVAL);
                animator.setDuration(ANIMATOR_DURATION);
                animator.start();

                break;
            case 1:
                animator = ObjectAnimator.ofFloat(car, "x", car.getX() + SNAP_GRID_INTERVAL);
                animator.setDuration(ANIMATOR_DURATION);
                animator.start();
                break;
            case 2:
                animator = ObjectAnimator.ofFloat(car, "y", car.getY() + SNAP_GRID_INTERVAL);
                animator.setDuration(ANIMATOR_DURATION);
                animator.start();
                break;
            case 3:
                animator = ObjectAnimator.ofFloat(car, "x", car.getX() - SNAP_GRID_INTERVAL);
                animator.setDuration(ANIMATOR_DURATION);
                animator.start();
                break;
            default:
                // Shouldn't reach this case
                break;
        }

        telemetryStatus.setText(String.valueOf(teleX).concat(", ").concat(String.valueOf(teleY+=10)));


    }

    private void reverseButtonEvent() {
        //byte[] bytes = commands.get("reverse").getBytes(Charset.defaultCharset());
        byte[] bytes = String.valueOf("ARD|MOVEMENT|S").getBytes();
        ServiceBluetooth.writeMsg(bytes);

        sendLog.append("ARD|MOVEMENT|S"+"\n");
        sendLog.setSelection(sendLog.getText().length());


        int orientation = (int) car.getRotation();
        ObjectAnimator animator;
        switch (((orientation / 90) % 4 + 4) % 4) {
            case 0:
                animator = ObjectAnimator.ofFloat(car, "y", car.getY() + SNAP_GRID_INTERVAL);
                animator.setDuration(ANIMATOR_DURATION);
                animator.start();
                break;
            case 1:
                animator = ObjectAnimator.ofFloat(car, "x", car.getX() - SNAP_GRID_INTERVAL);
                animator.setDuration(ANIMATOR_DURATION);
                animator.start();
                break;
            case 2:
                animator = ObjectAnimator.ofFloat(car, "y", car.getY() - SNAP_GRID_INTERVAL);
                animator.setDuration(ANIMATOR_DURATION);
                animator.start();
                break;
            case 3:
                animator = ObjectAnimator.ofFloat(car, "x", car.getX() + SNAP_GRID_INTERVAL);
                animator.setDuration(ANIMATOR_DURATION);
                animator.start();
                break;
            default:
                // Shouldn't reach this case
                break;
        }

        telemetryStatus.setText(String.valueOf(teleX).concat(", ").concat(String.valueOf(teleY-=10)));

    }

    private void turnRightButtonEvent() {
        //byte[] bytes = commands.get("turnRight").getBytes(Charset.defaultCharset());
        byte[] bytes = String.valueOf("ARD|MOVEMENT|E").getBytes();
        ServiceBluetooth.writeMsg(bytes);

        sendLog.append("ARD|MOVEMENT|E"+"\n");
        sendLog.setSelection(sendLog.getText().length());

        int orientation = (int) car.getRotation();

        ObjectAnimator animatorX;
        ObjectAnimator animatorY;
        ObjectAnimator animatorArc;
        ObjectAnimator rotateAnimator;
        AnimatorSet animatorSet = new AnimatorSet();
        Path path = new Path();

        switch (((orientation / 90) % 4 + 4) % 4) {
            case 0:
                animatorY = ObjectAnimator.ofFloat(car, "y", car.getY() - SNAP_GRID_INTERVAL);
                animatorY.setDuration(ANIMATOR_DURATION);

                path.arcTo(car.getX(),
                        car.getY() - SNAP_GRID_INTERVAL * 3,
                        car.getX() + SNAP_GRID_INTERVAL * 4,
                        car.getY() + SNAP_GRID_INTERVAL,
                        180f,
                        90f,
                        true);

                animatorArc = ObjectAnimator.ofFloat(car, View.X, View.Y, path);
                animatorArc.setDuration(ANIMATOR_DURATION);
                animatorArc.setStartDelay(ANIMATOR_DURATION);

                rotateAnimator = ObjectAnimator.ofFloat(car, "rotation", orientation, orientation + 90);
                rotateAnimator.setDuration(ANIMATOR_DURATION);
                rotateAnimator.setStartDelay(ANIMATOR_DURATION);

                animatorX = ObjectAnimator.ofFloat(car, "x", car.getX() + SNAP_GRID_INTERVAL * 3);
                animatorX.setDuration(ANIMATOR_DURATION);
                animatorX.setStartDelay(ANIMATOR_DURATION * 2);

                animatorSet.playTogether(animatorY, animatorArc, rotateAnimator, animatorX);
                animatorSet.start();
                break;
            case 1:
                animatorX = ObjectAnimator.ofFloat(car, "x", car.getX() + SNAP_GRID_INTERVAL);
                animatorX.setDuration(ANIMATOR_DURATION);

                path.arcTo(car.getX() - SNAP_GRID_INTERVAL,
                        car.getY(),
                        car.getX() + SNAP_GRID_INTERVAL * 3,
                        car.getY() + SNAP_GRID_INTERVAL * 4,
                        270f,
                        90f,
                        true);

                animatorArc = ObjectAnimator.ofFloat(car, View.X, View.Y, path);
                animatorArc.setDuration(ANIMATOR_DURATION);
                animatorArc.setStartDelay(ANIMATOR_DURATION);

                rotateAnimator = ObjectAnimator.ofFloat(car, "rotation", orientation, orientation + 90);
                rotateAnimator.setDuration(ANIMATOR_DURATION);
                rotateAnimator.setStartDelay(ANIMATOR_DURATION);

                animatorY = ObjectAnimator.ofFloat(car, "y", car.getY() + SNAP_GRID_INTERVAL * 3);
                animatorY.setDuration(ANIMATOR_DURATION);
                animatorY.setStartDelay(ANIMATOR_DURATION * 2);

                animatorSet.playTogether(animatorY, animatorArc, rotateAnimator, animatorX);
                animatorSet.start();
                break;
            case 2:
                animatorY = ObjectAnimator.ofFloat(car, "y", car.getY() + SNAP_GRID_INTERVAL);
                animatorY.setDuration(ANIMATOR_DURATION);

                path.arcTo(car.getX() - SNAP_GRID_INTERVAL * 4,
                        car.getY() + SNAP_GRID_INTERVAL,
                        car.getX(),
                        car.getY() + SNAP_GRID_INTERVAL * 3,
                        0f,
                        90f,
                        true);

                animatorArc = ObjectAnimator.ofFloat(car, View.X, View.Y, path);
                animatorArc.setDuration(ANIMATOR_DURATION);
                animatorArc.setStartDelay(ANIMATOR_DURATION);

                rotateAnimator = ObjectAnimator.ofFloat(car, "rotation", orientation, orientation + 90);
                rotateAnimator.setDuration(ANIMATOR_DURATION);
                rotateAnimator.setStartDelay(ANIMATOR_DURATION);

                animatorX = ObjectAnimator.ofFloat(car, "x", car.getX() - SNAP_GRID_INTERVAL * 3);
                animatorX.setDuration(ANIMATOR_DURATION);
                animatorX.setStartDelay(ANIMATOR_DURATION * 2);

                animatorSet.playTogether(animatorY, animatorArc, rotateAnimator, animatorX);
                animatorSet.start();
                break;
            case 3:
                animatorX = ObjectAnimator.ofFloat(car, "x", car.getX() - SNAP_GRID_INTERVAL);
                animatorX.setDuration(ANIMATOR_DURATION);

                path.arcTo(car.getX() - SNAP_GRID_INTERVAL * 3,
                        car.getY() - SNAP_GRID_INTERVAL * 4,
                        car.getX() + SNAP_GRID_INTERVAL,
                        car.getY(),
                        90f,
                        90f,
                        true);

                animatorArc = ObjectAnimator.ofFloat(car, View.X, View.Y, path);
                animatorArc.setDuration(ANIMATOR_DURATION);
                animatorArc.setStartDelay(ANIMATOR_DURATION);

                rotateAnimator = ObjectAnimator.ofFloat(car, "rotation", orientation, orientation + 90);
                rotateAnimator.setDuration(ANIMATOR_DURATION);
                rotateAnimator.setStartDelay(ANIMATOR_DURATION);

                animatorY = ObjectAnimator.ofFloat(car, "y", car.getY() - SNAP_GRID_INTERVAL * 3);
                animatorY.setDuration(ANIMATOR_DURATION);
                animatorY.setStartDelay(ANIMATOR_DURATION * 2);

                animatorSet.playTogether(animatorY, animatorArc, rotateAnimator, animatorX);
                animatorSet.start();
                break;
            default:
                // Shouldn't reach this case
                break;
        }
        telemetryStatus.setText(String.valueOf(teleX+=30).concat(", ").concat(String.valueOf(teleY+=30)));

    }

    private void turnLeftButtonEvent() {
        //byte[] bytes = commands.get("turnLeft").getBytes(Charset.defaultCharset());
        byte[] bytes = String.valueOf("ARD|MOVEMENT|Q").getBytes();
        ServiceBluetooth.writeMsg(bytes);

        sendLog.append("ARD|MOVEMENT|Q"+"\n");
        sendLog.setSelection(sendLog.getText().length());

        int orientation = (int) car.getRotation();

        ObjectAnimator animatorX;
        ObjectAnimator animatorY;
        ObjectAnimator animatorArc;
        ObjectAnimator rotateAnimator;
        AnimatorSet animatorSet = new AnimatorSet();
        Path path = new Path();

        switch (((orientation / 90) % 4 + 4) % 4) {
            case 0:
                animatorY = ObjectAnimator.ofFloat(car, "y", car.getY() - SNAP_GRID_INTERVAL);
                animatorY.setDuration(ANIMATOR_DURATION);

                path.arcTo(car.getX() - SNAP_GRID_INTERVAL * 4,
                        car.getY() - SNAP_GRID_INTERVAL * 3,
                        car.getX(),
                        car.getY() + SNAP_GRID_INTERVAL,
                        0f,
                        -90f,
                        true);

                animatorArc = ObjectAnimator.ofFloat(car, View.X, View.Y, path);
                animatorArc.setDuration(ANIMATOR_DURATION);
                animatorArc.setStartDelay(ANIMATOR_DURATION);

                rotateAnimator = ObjectAnimator.ofFloat(car, "rotation", orientation, orientation - 90);
                rotateAnimator.setDuration(ANIMATOR_DURATION);
                rotateAnimator.setStartDelay(ANIMATOR_DURATION);

                animatorX = ObjectAnimator.ofFloat(car, "x", car.getX() - SNAP_GRID_INTERVAL * 3);
                animatorX.setDuration(ANIMATOR_DURATION);
                animatorX.setStartDelay(ANIMATOR_DURATION * 2);

                animatorSet.playTogether(animatorY, animatorArc, rotateAnimator, animatorX);
                animatorSet.start();
                break;
            case 1:
                animatorX = ObjectAnimator.ofFloat(car, "x", car.getX() + SNAP_GRID_INTERVAL);
                animatorX.setDuration(ANIMATOR_DURATION);

                path.arcTo(car.getX() - SNAP_GRID_INTERVAL,
                        car.getY() - SNAP_GRID_INTERVAL * 4,
                        car.getX() + SNAP_GRID_INTERVAL * 3,
                        car.getY(),
                        90f,
                        -90f,
                        true);

                animatorArc = ObjectAnimator.ofFloat(car, View.X, View.Y, path);
                animatorArc.setDuration(ANIMATOR_DURATION);
                animatorArc.setStartDelay(ANIMATOR_DURATION);

                rotateAnimator = ObjectAnimator.ofFloat(car, "rotation", orientation, orientation - 90);
                rotateAnimator.setDuration(ANIMATOR_DURATION);
                rotateAnimator.setStartDelay(ANIMATOR_DURATION);

                animatorY = ObjectAnimator.ofFloat(car, "y", car.getY() - SNAP_GRID_INTERVAL * 3);
                animatorY.setDuration(ANIMATOR_DURATION);
                animatorY.setStartDelay(ANIMATOR_DURATION * 2);

                animatorSet.playTogether(animatorY, animatorArc, rotateAnimator, animatorX);
                animatorSet.start();
                break;
            case 2:
                animatorY = ObjectAnimator.ofFloat(car, "y", car.getY() + SNAP_GRID_INTERVAL);
                animatorY.setDuration(ANIMATOR_DURATION);

                path.arcTo(car.getX(),
                        car.getY() + SNAP_GRID_INTERVAL,
                        car.getX() + SNAP_GRID_INTERVAL * 4,
                        car.getY() + SNAP_GRID_INTERVAL * 3,
                        180f,
                        -90f,
                        true);

                animatorArc = ObjectAnimator.ofFloat(car, View.X, View.Y, path);
                animatorArc.setDuration(ANIMATOR_DURATION);
                animatorArc.setStartDelay(ANIMATOR_DURATION);

                rotateAnimator = ObjectAnimator.ofFloat(car, "rotation", orientation, orientation - 90);
                rotateAnimator.setDuration(ANIMATOR_DURATION);
                rotateAnimator.setStartDelay(ANIMATOR_DURATION);

                animatorX = ObjectAnimator.ofFloat(car, "x", car.getX() + SNAP_GRID_INTERVAL * 3);
                animatorX.setDuration(ANIMATOR_DURATION);
                animatorX.setStartDelay(ANIMATOR_DURATION * 2);

                animatorSet.playTogether(animatorY, animatorArc, rotateAnimator, animatorX);
                animatorSet.start();
                break;
            case 3:
                animatorX = ObjectAnimator.ofFloat(car, "x", car.getX() - SNAP_GRID_INTERVAL);
                animatorX.setDuration(ANIMATOR_DURATION);

                path.arcTo(car.getX() - SNAP_GRID_INTERVAL * 3,
                        car.getY(),
                        car.getX() + SNAP_GRID_INTERVAL,
                        car.getY() + SNAP_GRID_INTERVAL * 4,
                        270f,
                        -90f,
                        true);

                animatorArc = ObjectAnimator.ofFloat(car, View.X, View.Y, path);
                animatorArc.setDuration(ANIMATOR_DURATION);
                animatorArc.setStartDelay(ANIMATOR_DURATION);

                rotateAnimator = ObjectAnimator.ofFloat(car, "rotation", orientation, orientation - 90);
                rotateAnimator.setDuration(ANIMATOR_DURATION);
                rotateAnimator.setStartDelay(ANIMATOR_DURATION);

                animatorY = ObjectAnimator.ofFloat(car, "y", car.getY() + SNAP_GRID_INTERVAL * 3);
                animatorY.setDuration(ANIMATOR_DURATION);
                animatorY.setStartDelay(ANIMATOR_DURATION * 2);

                animatorSet.playTogether(animatorY, animatorArc, rotateAnimator, animatorX);
                animatorSet.start();
                break;
            default:
                // Shouldn't reach this case
                break;
        }
    }

    private void LeftReverseButton(){
        byte[] bytes = String.valueOf("ARD|MOVEMENT|A").getBytes();
        ServiceBluetooth.writeMsg(bytes);

        sendLog.append("ARD|MOVEMENT|A"+"\n");
        sendLog.setSelection(sendLog.getText().length());

        int orientation = (int) car.getRotation();

        ObjectAnimator animatorX;
        ObjectAnimator animatorY;
        ObjectAnimator animatorArc;
        ObjectAnimator rotateAnimator;
        AnimatorSet animatorSet = new AnimatorSet();
        Path path = new Path();

        switch (((orientation / 90) % 4 + 4) % 4) {
            case 0:
                animatorY = ObjectAnimator.ofFloat(car, "y", car.getY() + SNAP_GRID_INTERVAL);
                animatorY.setDuration(ANIMATOR_DURATION);

                path.arcTo(car.getX()- SNAP_GRID_INTERVAL * 4,
                        car.getY() - SNAP_GRID_INTERVAL,
                        car.getX(),
                        car.getY() + SNAP_GRID_INTERVAL * 3,
                        0f,
                        90f,
                        true);

                animatorArc = ObjectAnimator.ofFloat(car, View.X, View.Y, path);
                animatorArc.setDuration(ANIMATOR_DURATION);
                animatorArc.setStartDelay(ANIMATOR_DURATION);

                rotateAnimator = ObjectAnimator.ofFloat(car, "rotation", orientation, orientation + 90);
                rotateAnimator.setDuration(ANIMATOR_DURATION);
                rotateAnimator.setStartDelay(ANIMATOR_DURATION);

                animatorX = ObjectAnimator.ofFloat(car, "x", car.getX() - SNAP_GRID_INTERVAL * 3);
                animatorX.setDuration(ANIMATOR_DURATION);
                animatorX.setStartDelay(ANIMATOR_DURATION * 2);

                animatorSet.playTogether(animatorY, animatorArc, rotateAnimator, animatorX);
                animatorSet.start();

                break;
            case 1:
                animatorX = ObjectAnimator.ofFloat(car, "x", car.getX() - SNAP_GRID_INTERVAL);
                animatorX.setDuration(ANIMATOR_DURATION);

                path.arcTo(car.getX() - SNAP_GRID_INTERVAL * 3,
                        car.getY() - SNAP_GRID_INTERVAL * 4,
                        car.getX() + SNAP_GRID_INTERVAL,
                        car.getY(),
                        90f,
                        90f,
                        true);

                animatorArc = ObjectAnimator.ofFloat(car, View.X, View.Y, path);
                animatorArc.setDuration(ANIMATOR_DURATION);
                animatorArc.setStartDelay(ANIMATOR_DURATION);

                rotateAnimator = ObjectAnimator.ofFloat(car, "rotation", orientation, orientation + 90);
                rotateAnimator.setDuration(ANIMATOR_DURATION);
                rotateAnimator.setStartDelay(ANIMATOR_DURATION);

                animatorY = ObjectAnimator.ofFloat(car, "y", car.getY() - SNAP_GRID_INTERVAL * 3);
                animatorY.setDuration(ANIMATOR_DURATION);
                animatorY.setStartDelay(ANIMATOR_DURATION * 2);

                animatorSet.playTogether(animatorY, animatorArc, rotateAnimator, animatorX);
                animatorSet.start();
                break;
            case 2:
                animatorY = ObjectAnimator.ofFloat(car, "y", car.getY() - SNAP_GRID_INTERVAL);
                animatorY.setDuration(ANIMATOR_DURATION);

                path.arcTo(car.getX(),
                        car.getY() - SNAP_GRID_INTERVAL * 3,
                        car.getX() + SNAP_GRID_INTERVAL * 4,
                        car.getY() - SNAP_GRID_INTERVAL,
                        180f,
                        90f,
                        true);

                animatorArc = ObjectAnimator.ofFloat(car, View.X, View.Y, path);
                animatorArc.setDuration(ANIMATOR_DURATION);
                animatorArc.setStartDelay(ANIMATOR_DURATION);

                rotateAnimator = ObjectAnimator.ofFloat(car, "rotation", orientation, orientation + 90);
                rotateAnimator.setDuration(ANIMATOR_DURATION);
                rotateAnimator.setStartDelay(ANIMATOR_DURATION);

                animatorX = ObjectAnimator.ofFloat(car, "x", car.getX() + SNAP_GRID_INTERVAL * 3);
                animatorX.setDuration(ANIMATOR_DURATION);
                animatorX.setStartDelay(ANIMATOR_DURATION * 2);

                animatorSet.playTogether(animatorY, animatorArc, rotateAnimator, animatorX);
                animatorSet.start();
                break;
            case 3:
                animatorX = ObjectAnimator.ofFloat(car, "x", car.getX() + SNAP_GRID_INTERVAL);
                animatorX.setDuration(ANIMATOR_DURATION);

                path.arcTo(car.getX() - SNAP_GRID_INTERVAL,
                        car.getY(),
                        car.getX() + SNAP_GRID_INTERVAL * 3,
                        car.getY() + SNAP_GRID_INTERVAL * 4,
                        270f,
                        90f,
                        true);

                animatorArc = ObjectAnimator.ofFloat(car, View.X, View.Y, path);
                animatorArc.setDuration(ANIMATOR_DURATION);
                animatorArc.setStartDelay(ANIMATOR_DURATION);

                rotateAnimator = ObjectAnimator.ofFloat(car, "rotation", orientation, orientation + 90);
                rotateAnimator.setDuration(ANIMATOR_DURATION);
                rotateAnimator.setStartDelay(ANIMATOR_DURATION);

                animatorY = ObjectAnimator.ofFloat(car, "y", car.getY() + SNAP_GRID_INTERVAL * 3);
                animatorY.setDuration(ANIMATOR_DURATION);
                animatorY.setStartDelay(ANIMATOR_DURATION * 2);

                animatorSet.playTogether(animatorY, animatorArc, rotateAnimator, animatorX);
                animatorSet.start();
                break;
            default:
                // Shouldn't reach this case
                break;
        }

    }

    private void RightReverseButton(){
        byte[] bytes = String.valueOf("ARD|MOVEMENT|D").getBytes();
        ServiceBluetooth.writeMsg(bytes);

        sendLog.append("ARD|MOVEMENT|D"+"\n");
        sendLog.setSelection(sendLog.getText().length());

        int orientation = (int) car.getRotation();

        ObjectAnimator animatorX;
        ObjectAnimator animatorY;
        ObjectAnimator animatorArc;
        ObjectAnimator rotateAnimator;
        AnimatorSet animatorSet = new AnimatorSet();
        Path path = new Path();

        switch (((orientation / 90) % 4 + 4) % 4) {
            case 0:
                animatorY = ObjectAnimator.ofFloat(car, "y", car.getY() + SNAP_GRID_INTERVAL);
                animatorY.setDuration(ANIMATOR_DURATION);

                path.arcTo(car.getX(),
                        car.getY() - SNAP_GRID_INTERVAL,
                        car.getX() + SNAP_GRID_INTERVAL * 4,
                        car.getY() + SNAP_GRID_INTERVAL * 3,
                        180f,
                        -90f,
                        true);

                animatorArc = ObjectAnimator.ofFloat(car, View.X, View.Y, path);
                animatorArc.setDuration(ANIMATOR_DURATION);
                animatorArc.setStartDelay(ANIMATOR_DURATION);

                rotateAnimator = ObjectAnimator.ofFloat(car, "rotation", orientation, orientation - 90);
                rotateAnimator.setDuration(ANIMATOR_DURATION);
                rotateAnimator.setStartDelay(ANIMATOR_DURATION);

                animatorX = ObjectAnimator.ofFloat(car, "x", car.getX() + SNAP_GRID_INTERVAL * 3);
                animatorX.setDuration(ANIMATOR_DURATION);
                animatorX.setStartDelay(ANIMATOR_DURATION * 2);

                animatorSet.playTogether(animatorY, animatorArc, rotateAnimator, animatorX);
                animatorSet.start();
                break;
            case 1:
                animatorX = ObjectAnimator.ofFloat(car, "x", car.getX() - SNAP_GRID_INTERVAL);
                animatorX.setDuration(ANIMATOR_DURATION);

                path.arcTo(car.getX() - SNAP_GRID_INTERVAL * 3,
                        car.getY(),
                        car.getX() + SNAP_GRID_INTERVAL,
                        car.getY() + SNAP_GRID_INTERVAL * 4,
                        270f,
                        -90f,
                        true);

                animatorArc = ObjectAnimator.ofFloat(car, View.X, View.Y, path);
                animatorArc.setDuration(ANIMATOR_DURATION);
                animatorArc.setStartDelay(ANIMATOR_DURATION);

                rotateAnimator = ObjectAnimator.ofFloat(car, "rotation", orientation, orientation - 90);
                rotateAnimator.setDuration(ANIMATOR_DURATION);
                rotateAnimator.setStartDelay(ANIMATOR_DURATION);

                animatorY = ObjectAnimator.ofFloat(car, "y", car.getY() + SNAP_GRID_INTERVAL * 3);
                animatorY.setDuration(ANIMATOR_DURATION);
                animatorY.setStartDelay(ANIMATOR_DURATION * 2);

                animatorSet.playTogether(animatorY, animatorArc, rotateAnimator, animatorX);
                animatorSet.start();
                break;
            case 2:
                animatorY = ObjectAnimator.ofFloat(car, "y", car.getY() - SNAP_GRID_INTERVAL);
                animatorY.setDuration(ANIMATOR_DURATION);

                path.arcTo(car.getX() - SNAP_GRID_INTERVAL * 4,
                        car.getY() - SNAP_GRID_INTERVAL * 3,
                        car.getX(),
                        car.getY() - SNAP_GRID_INTERVAL,
                        0f,
                        -90f,
                        true);

                animatorArc = ObjectAnimator.ofFloat(car, View.X, View.Y, path);
                animatorArc.setDuration(ANIMATOR_DURATION);
                animatorArc.setStartDelay(ANIMATOR_DURATION);

                rotateAnimator = ObjectAnimator.ofFloat(car, "rotation", orientation, orientation - 90);
                rotateAnimator.setDuration(ANIMATOR_DURATION);
                rotateAnimator.setStartDelay(ANIMATOR_DURATION);

                animatorX = ObjectAnimator.ofFloat(car, "x", car.getX() - SNAP_GRID_INTERVAL * 3);
                animatorX.setDuration(ANIMATOR_DURATION);
                animatorX.setStartDelay(ANIMATOR_DURATION * 2);

                animatorSet.playTogether(animatorY, animatorArc, rotateAnimator, animatorX);
                animatorSet.start();
                break;
            case 3:
                animatorX = ObjectAnimator.ofFloat(car, "x", car.getX() + SNAP_GRID_INTERVAL);
                animatorX.setDuration(ANIMATOR_DURATION);

                path.arcTo(car.getX() - SNAP_GRID_INTERVAL,
                        car.getY() - SNAP_GRID_INTERVAL * 4,
                        car.getX() + SNAP_GRID_INTERVAL * 3,
                        car.getY(),
                        90f,
                        -90f,
                        true);

                animatorArc = ObjectAnimator.ofFloat(car, View.X, View.Y, path);
                animatorArc.setDuration(ANIMATOR_DURATION);
                animatorArc.setStartDelay(ANIMATOR_DURATION);

                rotateAnimator = ObjectAnimator.ofFloat(car, "rotation", orientation, orientation - 90);
                rotateAnimator.setDuration(ANIMATOR_DURATION);
                rotateAnimator.setStartDelay(ANIMATOR_DURATION);

                animatorY = ObjectAnimator.ofFloat(car, "y", car.getY() - SNAP_GRID_INTERVAL * 3);
                animatorY.setDuration(ANIMATOR_DURATION);
                animatorY.setStartDelay(ANIMATOR_DURATION * 2);

                animatorSet.playTogether(animatorY, animatorArc, rotateAnimator, animatorX);
                animatorSet.start();
                break;
            default:
                // Shouldn't reach this case
                break;
        }
    }

    //set the target ID text in the white color;
    private void setObstacleID(int obstacleNumber, String imageID){
        TextView obstacleID = (TextView)obstacles.get(obstacleNumber).getChildAt(2);
        obstacleID.setTextColor(getResources().getColor(R.color.light_blue_300));
        obstacleID.setText(imageID);

        if (imageID.equals("bulls")) {
            Drawable drawable = getResources().getDrawable(R.drawable.bullseye);

            // Calculate the desired width and height of the drawable
            int desiredWidth = obstacleID.getWidth();
            int desiredHeight = obstacleID.getHeight();

            // Scale the drawable to fit the TextView
            drawable.setBounds(0, 0, desiredWidth, desiredHeight);

            // Set the drawable to the left of the text
            obstacleID.setCompoundDrawables(drawable, null, null, null);
        }

        if (imageID.equals("left")) {
            Drawable drawable = getResources().getDrawable(R.drawable.arrow_left);

            // Calculate the desired width and height of the drawable
            int desiredWidth = obstacleID.getWidth();
            int desiredHeight = obstacleID.getHeight();

            // Scale the drawable to fit the TextView
            drawable.setBounds(0, 0, desiredWidth, desiredHeight);

            // Set the drawable to the left of the text
            obstacleID.setCompoundDrawables(drawable, null, null, null);
        }

        if (imageID.equals("right")) {
            Drawable drawable = getResources().getDrawable(R.drawable.arrow_right);

            // Calculate the desired width and height of the drawable
            int desiredWidth = obstacleID.getWidth();
            int desiredHeight = obstacleID.getHeight();

            // Scale the drawable to fit the TextView
            drawable.setBounds(0, 0, desiredWidth, desiredHeight);

            // Set the drawable to the left of the text
            obstacleID.setCompoundDrawables(drawable, null, null, null);
        }




    }

    private void updateRobotPosition(int x, int y, char direction) {
        // Convert grid coordinates to pixel coordinates
        // Snap grid interval
        int snapGridInterval = 40;

        // Convert grid coordinates to pixel coordinates
        int pixelX = x * snapGridInterval;
        int pixelY = (17 - y) * snapGridInterval;

        // Snap to the nearest grid cell
        pixelX = (int) (Math.round((double) pixelX / snapGridInterval) * snapGridInterval);
        pixelY = (int) (Math.round((double) pixelY / snapGridInterval) * snapGridInterval);

        // Update car position based on direction
        switch (direction) {
            case 'N':
                car.setRotation(0);
                break;
            case 'E':
                car.setRotation(90);
                break;
            case 'S':
                car.setRotation(180);
                break;
            case 'W':
                car.setRotation(270);
                break;
            default:
                // Shouldn't reach this case
                break;
        }

        // Set car position
        car.setX(pixelX);
        car.setY(pixelY);

        // Update telemetry status (optional)
        telemetryStatus.setText("X: " + x + ", Y: " + y + ", Direction: " + direction);
    }
    //set a Dialog caller
    public void showMyDialog() {
        PutObstacleDialog dialogFragment = new PutObstacleDialog();
        dialogFragment.setTargetFragment(this, 0); // Set the target fragment
        dialogFragment.show(getFragmentManager(), "MyDialogFragment");
    }

    // Receive values from the dialog and update the FrameLayout position
    public void applyValues(String obsnum, String xValue, String yValue, String facing) {

        float x = Float.parseFloat(xValue);
        float y = Float.parseFloat(yValue);
        float direction = Float.parseFloat(facing);
        int obnum = Integer.parseInt(obsnum);
        obstacles.get(obnum).setX(x*SNAP_GRID_INTERVAL);
        obstacles.get(obnum).setY((19-y)*SNAP_GRID_INTERVAL);

        obstacles.get(obnum).getChildAt(1).setPivotX(obstacles.get(obnum).getWidth()/2.0f);
        obstacles.get(obnum).getChildAt(1).setPivotY(obstacles.get(obnum).getHeight()/2.0f);

        // sus working code lol
        obstacles.get(obnum).getChildAt(1).setRotation((90 - direction) % 360);



//        sendObstaclesOneTime(obnum);
    }

    private void putObstaclesButtonEvent(){
        showMyDialog();
    }


    @Override
    public void onResume() {
        super.onResume();
        // Register broadcast receiver to receive selected Bluetooth device
        LocalBroadcastManager.getInstance(requireContext()).registerReceiver(deviceSelectedReceiver, new IntentFilter("btDeviceSelected"));
    }

    @Override
    public void onPause() {
        super.onPause();
        // Unregister broadcast receiver
        LocalBroadcastManager.getInstance(requireContext()).unregisterReceiver(deviceSelectedReceiver);
    }

    // BroadcastReceiver to receive selected Bluetooth device
    private BroadcastReceiver deviceSelectedReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            if (intent.getAction() != null && intent.getAction().equals("btDeviceSelected")) {
                // Get the selected device and its name from the broadcast
//                BluetoothDevice selectedDevice = intent.getParcelableExtra("SelectedDevice");
                String selectedDeviceName = intent.getStringExtra("SelectedDeviceName");

                // Update UI with the selected device's name
                btStatus.setText(selectedDeviceName);
            }
        }
    };

    //Broadcast Receiver for incoming message
    BroadcastReceiver myReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
//            Log.d("Message", "Receiving Message!");
//
//            String message = intent.getStringExtra("receivingMsg").trim();
//
//            Log.d("msg", message);



//            if(!message.equals(lastReceivedMessage)){
//                String command = message.substring(0, message.indexOf(','));
//
//                String[] parts = message.split(",");
//
//                switch (command) {
//                    case "ROBOT":
//
//                        int x = Integer.parseInt(parts[1]);
//                        int y = Integer.parseInt(parts[2]);
//                        char direction = parts[3].charAt(0);
//
//                        Log.d("ROBOT", "(x: " + x + ") (y: " + y + ") (direction: " + direction + ")");
//
//
//
//                        updateRobotPosition(x, y, direction);
//                        break;
//
//                    //car status receiver part and corresponding textview box for this;
//                    case "STATUS":
//                        String status = message.substring((message.indexOf(',') + 1));
//                        break;
//
//                    case "TARGET":
//
//                        int obstacleNumber = Integer.parseInt(parts[1]);
//                        String imageID = parts[2];
//
//                        //int obstacleNumber = Character.getNumericValue(message.charAt(7));
//
//                        //String imageID = message.substring(9);
//
//
//                        //ALG|Detections|obstacleNumber, imageID
//
//
//                        if(!checkUpdate[obstacleNumber - 1].equals(imageID)){
//                            Log.d("TARGET", "(obstacleNumber: " + obstacleNumber + ") (targetId: " + imageID + ")");
//
//                            //setObstacleImage(obstacleNumber,targetId);
//                            //update the obstacle with updating textview;
//                            setObstacleID(obstacleNumber,imageID);
//
//                            StringBuilder stringBack = new StringBuilder();
//                            stringBack.append("Target ")
//                                    .append(obstacleNumber)
//                                    .append(" updated successfully");
//
//                            byte[] bytes = stringBack.toString().getBytes(Charset.defaultCharset());
//                            ServiceBluetooth.writeMsg(bytes);
//
//                            stringBack.setLength(0);
//
//                            checkUpdate[obstacleNumber - 1] = imageID;
//                        }
//
//                        break;
//                    default:
//                        break;
//                }
//            }
//            lastReceivedMessage = message;


            String message = intent.getStringExtra("receivingMsg").trim();

// Find the index of '|' after "ALG"
            int pipeIndex = message.indexOf('|');

// Extract the substring starting from the character after the first '|'
            String desiredSubstring = message.substring(pipeIndex + 1);

// Find the index of '|' within the desired substring
            int nextPipeIndex = desiredSubstring.indexOf('|');

// Extract the part before the next '|' which is the action part (PathHist, STATUS, Detections, etc.)
            String actionPart = desiredSubstring.substring(0, nextPipeIndex);

// Extract the part starting from the next '|' which contains the arrays like "[[10,10,N], [11, 39, N], ...]"
            String arraysPart = desiredSubstring.substring(nextPipeIndex + 1);

// Remove leading '[' and trailing ']' and split by '], [' to get individual array strings
            String[] arrayStrings = arraysPart.substring(2, arraysPart.length() - 2).split("\\], \\[");

// Now, let's handle different cases based on the actionPart
            switch (actionPart) {
                case "PathHist":
                    // Iterate through arrayStrings to extract values
                    for (String arrayString : arrayStrings) {
                        // Split the arrayString by ',' to get individual values
                        String[] values = arrayString.split(",");

                        // Now you have the individual values
                        int x = Integer.parseInt(values[0].trim());
                        int y = Integer.parseInt(values[1].trim());
                        char direction = values[2].trim().charAt(0);

                        // Now you can use these values according to your logic
                        updateRobotPosition(x, y, direction);
                        Log.d("telemetry from rpi", "X: " + x + " ,Y: " + y + " ,Direction:  " + direction +"\n");
                        sendLog.append("X: " + x + " ,Y: " + y + " ,Direction:  " + direction +"\n");
                    }
                    break;

                case "STATUS":
                    // Handle STATUS action
                    String status = message.substring(message.indexOf('|', message.indexOf('|') + 1) + 1);
                    Log.d("STREAM STATUS", status);
                    break;

                case "Detections":
                    // Extract obstacleNumber and imageID
                    String[] values = arraysPart.substring(1, arraysPart.length() - 1).split(",");
                    int obstacleNumber = Integer.parseInt(values[0].trim());
                    String imageID = values[1].trim();

                    // Handle Detections action
                    if (!checkUpdate[obstacleNumber - 1].equals(imageID)) {
                        Log.d("TARGET", "(obstacleNumber: " + obstacleNumber + ") (targetId: " + imageID + ")");
                        setObstacleID(obstacleNumber, imageID);

                        // Send response
                        StringBuilder response = new StringBuilder("RSP|Detections|[");
                        response.append(obstacleNumber).append(",").append(imageID).append("]");
                        byte[] bytes = response.toString().getBytes(Charset.defaultCharset());
                        ServiceBluetooth.writeMsg(bytes);

                        checkUpdate[obstacleNumber - 1] = imageID;
                    }
                    break;

                default:
                    break;

            }



        }
    };
}