package com.sc2079.mdp28;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Bundle;
import android.os.Handler;
import android.os.SystemClock;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TableLayout;
import android.widget.TableRow;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;

import java.nio.charset.Charset;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

public class ZoomFragment extends Fragment {

    Button startBtn, task2ConnectBtn, stopBtn;
    TableLayout logTable;
    private List<String> logList = new ArrayList<>();


    private TextView task2Timer, connection;
    private Handler handler;
    private long startTime = 0L;
    private long elapsedTime = 0L;
    private final int REFRESH_RATE = 50;


    private static final UUID myUUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");


    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        // Inflate the layout for this fragment
        View view = inflater.inflate(R.layout.fragment_zoom, container, false);
        // Initialize the button
        startBtn = view.findViewById(R.id.startTask);
        task2ConnectBtn = view.findViewById(R.id.task2ConnectBtn);
        stopBtn = view.findViewById(R.id.stopTask);
        logTable = view.findViewById(R.id.logTable);
        connection = view.findViewById(R.id.connection);
        return view;
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        handler = new Handler();


        task2Timer = view.findViewById(R.id.task2Timer);

        // Set OnClickListener for the button
        startBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                resetTimer();
                startTime = SystemClock.uptimeMillis();
                handler.postDelayed(updateTimer, 0);

                StringBuilder strBuilder =  new StringBuilder();
                strBuilder.append("RSP|Start|");
                Toast.makeText(getActivity(), strBuilder.toString(), Toast.LENGTH_LONG).show();
                byte[] bytes = strBuilder.toString().getBytes(Charset.defaultCharset());
                ServiceBluetooth.writeMsg(bytes);

            }
        });

        task2ConnectBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
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

            }
        });

        stopBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                Log.d("TASK 2 STATUS", "stop pressed");
                elapsedTime = SystemClock.uptimeMillis() - startTime;
                handler.removeCallbacks(updateTimer);
                addLog("Task completed in: " + formatElapsedTime(elapsedTime));

            }
        });

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

    private BroadcastReceiver deviceSelectedReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            if (intent.getAction() != null && intent.getAction().equals("btDeviceSelected")) {
                // Get the selected device and its name from the broadcast
//                BluetoothDevice selectedDevice = intent.getParcelableExtra("SelectedDevice");
                String selectedDeviceName = intent.getStringExtra("SelectedDeviceName");

                // Update UI with the selected device's name
                connection.setText(selectedDeviceName);
            }
        }
    };

    private String formatElapsedTime(long elapsedTime) {
        int secs = (int) (elapsedTime / 1000);
        int mins = secs / 60;
        secs = secs % 60;
        int milliseconds = (int) (elapsedTime % 1000);
        return mins + " minutes, " + secs + " seconds, " + milliseconds + " milliseconds";
    }


    private String getCurrentTime() {
        SimpleDateFormat sdf = new SimpleDateFormat("mm:ss", Locale.getDefault());
        return sdf.format(new Date());
    }
    private void addLog(String log) {
        logList.add(log);
        updateLogTable();
    }

    private void updateLogTable() {
        logTable.removeAllViews();
        for (String log : logList) {
            TableRow row = new TableRow(getActivity());
            TextView textView = new TextView(getActivity());
            textView.setText(log);
            row.addView(textView);
            logTable.addView(row);
        }
    }

    private Runnable updateTimer = new Runnable() {
        public void run() {
            long updatedTime = SystemClock.uptimeMillis() - startTime + elapsedTime;
            int secs = (int) (updatedTime / 1000);
            int mins = secs / 60;
            secs = secs % 60;
            int milliseconds = (int) (updatedTime % 1000);
            task2Timer.setText("" + mins + ":" + String.format("%02d", secs) + ":" + String.format("%03d", milliseconds));
            handler.postDelayed(this, REFRESH_RATE);
        }
    };

    private void resetTimer() {
        startTime = SystemClock.uptimeMillis();
        elapsedTime = 0L;
        task2Timer.setText("00:00:000");
    }





}




