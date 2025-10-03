package com.sc2079.mdp28;

import android.app.IntentService;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothServerSocket;
import android.bluetooth.BluetoothSocket;
import android.content.Context;
import android.content.Intent;
import android.os.Handler;
import android.util.Log;
import android.widget.Toast;

import androidx.annotation.Nullable;
import androidx.localbroadcastmanager.content.LocalBroadcastManager;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.Charset;
import java.util.UUID;

public class ServiceBluetooth extends IntentService {
    private static final String TAG = "BtService";
    private static final String NAME = "MDPTest";



    // BLuetooth comms
    private static final String TAG2 = "BluetoothChat";


    // Declarations
    private static Context myContext;
    private static BluetoothSocket mySocket;
    private static InputStream myInputStream;
    private static OutputStream myOutPutStream;
    private static BluetoothDevice myBtConnectionDevice;



    /**
     * @param
     *
     */
    private BluetoothDevice mmDevice;
    private BluetoothAdapter mBluetoothAdapter;
    private AcceptThread myAcceptThread;
    private ConnectThread mConnectThread;
    private static final UUID myUUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");
    private UUID deviceUUID;
    Context mContext;

    private Handler reconnectHandler = new Handler();
    private static final long RECONNECT_DELAY = 1000; // Delay for 5 seconds

    private int reconnectAttempts = 0;
    private static final int MAX_RECONNECT_ATTEMPTS = 2;

    //reconnect mechanism
    private Runnable reconnectRunnable = new Runnable() {
        @Override
        public void run() {
            if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
                showToast("Max reconnect attempts reached. Stopping reconnection.");
                return;
            }

            if (mmDevice != null) {
                reconnectAttempts++; // Increase the reconnect attempt count
                showToast("Attempting to reconnect. Attempt " + reconnectAttempts + " of " + MAX_RECONNECT_ATTEMPTS);
                startClient(mmDevice, deviceUUID);
            } else {
                showToast("Device not available. Retrying in " + (RECONNECT_DELAY / 1000) + " seconds.");
                reconnectHandler.postDelayed(this, RECONNECT_DELAY * (reconnectAttempts + 1)); // Increase delay progressively
            }
        }
    };

    // Method to show toast messages
    private void showToast(String message) {
        Handler mainHandler = new Handler(mContext.getMainLooper());
        mainHandler.post(() -> {
            Toast.makeText(mContext, message, Toast.LENGTH_SHORT).show();
        });
    }


    public ServiceBluetooth() {
        super("BTService");
    }

    @Override
    protected void onHandleIntent(@Nullable Intent intent) {
        mContext = getApplicationContext();
        mBluetoothAdapter = BluetoothAdapter.getDefaultAdapter();

        if (intent.getStringExtra("serviceType").equals("listen")) {
            mmDevice = (BluetoothDevice) intent.getExtras().getParcelable("device");
            Log.d(TAG, "Service Handle: startAcceptThread");
            startAcceptThread();
        } else {
            mmDevice = (BluetoothDevice) intent.getExtras().getParcelable("device");
            deviceUUID = (UUID) intent.getSerializableExtra("id");
            Log.d(TAG, "Service Handle: startClientThread "+mmDevice.getName()+" UUID:"+deviceUUID.toString());
            startClient(mmDevice, deviceUUID);
        }
    }
    /**
     * Thread acts as server.Listening for connections.
     */
    private class AcceptThread extends Thread {
        private final BluetoothServerSocket mmServerSocket;

        public AcceptThread() {
            // Use a temporary object that is later assigned to mmServerSocket
            // because mmServerSocket is final.
            BluetoothServerSocket tmp = null;
            try {
                // MY_UUID is the app's UUID string, also used by the client code.
                tmp = mBluetoothAdapter.listenUsingRfcommWithServiceRecord(NAME, myUUID);
            } catch (IOException e) {
                Log.e(TAG, "Socket's listen() method failed", e);
            }
            mmServerSocket = tmp;
        }

        public void run() {

            Log.d(TAG, "AcceptThread: Running");

            BluetoothSocket socket;
            Intent connectionStatusIntent;

            try {

                Log.d(TAG, "Run: RFCOM server socket start....");

                // Blocking call which will only return on a successful connection / exception
                socket = mmServerSocket.accept();

                // Broadcast connection message
                connectionStatusIntent = new Intent("btConnectionStatus");
                connectionStatusIntent.putExtra("ConnectionStatus", "connect");
                connectionStatusIntent.putExtra("Device", BluetoothFragment.getBluetoothDevice());
                LocalBroadcastManager.getInstance(mContext).sendBroadcast(connectionStatusIntent);

                // Successfully connected
                Log.d(TAG, "Run: RFCOM server socket accepted connection");

                // Start BluetoothChat
                ServiceBluetooth.connected(socket, mmDevice, mContext);


            } catch (IOException e) {
                connectionStatusIntent = new Intent("btConnectionStatus");
                connectionStatusIntent.putExtra("ConnectionStatus", "connectionFail");
                connectionStatusIntent.putExtra("Device", BluetoothFragment.getBluetoothDevice());
                Log.d(TAG, "AcceptThread: Connection Failed ,IOException: " + e.getMessage());
                // Start reconnecting mechanism
                reconnectHandler.postDelayed(reconnectRunnable, RECONNECT_DELAY);
            }


            Log.d(TAG, "Ended AcceptThread");

        }

        // Closes the connect socket and causes the thread to finish.
        public void cancel() {
            Log.d(TAG, "Cancel: Canceling AcceptThread");

            try {
                mmServerSocket.close();
            } catch (IOException e) {
                Log.d(TAG, "Cancel: Closing AcceptThread Failed. " + e.getMessage());
            }
        }
    }


    /**
     * Connect as client
     *
     */
    private class ConnectThread extends Thread {
        private BluetoothSocket mmSocket;

        public ConnectThread(BluetoothDevice device, UUID uuid) {
            Log.d(TAG, "ConnectThread: started.");
            mmDevice = device;
            deviceUUID = uuid;
        }

        public void run() {
            BluetoothSocket temp = null;
            Intent connectionStatusIntent;

            Log.d(TAG, "Run: myConnectThread");

            // BluetoothSocket for connection with given BluetoothDevice
            try {
                Log.d(TAG, "ConnectThread: Trying to create InsecureRFcommSocket to "+mmDevice.getName()+" using UUID: " +
                        myUUID);
                temp = mmDevice.createRfcommSocketToServiceRecord(deviceUUID);
            } catch (IOException e) {

                Log.d(TAG, "ConnectThread: Could not create InsecureRFcommSocket " + e.getMessage());
            }

            mmSocket = temp;

            // Cancel discovery to prevent slow connection
            mBluetoothAdapter.cancelDiscovery();

            try {

                Log.d(TAG, "Connecting to Device: " + mmDevice);
                // Blocking call and will only return on a successful connection / exception
                mmSocket.connect();


                // Broadcast connection message
                connectionStatusIntent = new Intent("btConnectionStatus");
                connectionStatusIntent.putExtra("ConnectionStatus", "connect");
                connectionStatusIntent.putExtra("Device", mmDevice);
                LocalBroadcastManager.getInstance(mContext).sendBroadcast(connectionStatusIntent);

                Log.d(TAG, "run: ConnectThread connected");

                // Start BluetoothChat
                ServiceBluetooth.connected(mmSocket, mmDevice, mContext);

                // Cancel myAcceptThread for listening
                if (myAcceptThread != null) {
                    myAcceptThread.cancel();
                    myAcceptThread = null;
                }

            } catch (IOException e) {
                try {
                    mmSocket.close();
                    connectionStatusIntent = new Intent("btConnectionStatus");
                    connectionStatusIntent.putExtra("ConnectionStatus", "connectionFail");
                    connectionStatusIntent.putExtra("Device", mmDevice);
                    LocalBroadcastManager.getInstance(mContext).sendBroadcast(connectionStatusIntent);
                    Log.d(TAG, "run: Socket Closed: Connection Failed!! " + e.getMessage());
                } catch (IOException e1) {
                    Log.d(TAG, "myConnectThread, run: Unable to close socket connection: " + e1.getMessage());
                }
                // Start reconnecting mechanism
                reconnectHandler.postDelayed(reconnectRunnable, RECONNECT_DELAY);
            }

            catch (NullPointerException e) {
                e.printStackTrace();
            }
        }




        // Closes the client socket and causes the thread to finish.
        public void cancel() {
            try {
                Log.d(TAG, "Cancel: Closing Client Socket");
                mmSocket.close();
            } catch (IOException e) {
                Log.d(TAG, "Cancel: Closing mySocket in ConnectThread Failed " + e.getMessage());
            }
        }
    }


    /**
     * Start the chat service. Specifically start AcceptThread to begin a
     * session in listening (server) mode. Called by the Activity onResume()
     */
    public synchronized void startAcceptThread() {
        Log.d(TAG, "start");

        // Cancel any thread attempting to make a connection
        if (mConnectThread != null) {
            mConnectThread.cancel();
            mConnectThread = null;
        }
        if (myAcceptThread == null) {
            myAcceptThread = new AcceptThread();
            myAcceptThread.start();
        }
    }

    /**
     AcceptThread starts and sits waiting for a connection.
     Then ConnectThread starts and attempts to make a connection with the other devices AcceptThread.
     **/

    public void startClient(BluetoothDevice device,UUID uuid){
        Log.d(TAG, "startClient: Started.");
        mConnectThread = new ConnectThread(device, uuid);
        mConnectThread.start();
    }

    //Bluetooth comms methods
    public static BluetoothDevice getBluetoothDevice(){
        return myBtConnectionDevice;
    }

    // Start Bluetooth Chat
    public static void startComms(BluetoothSocket socket) {

        Log.d(TAG2, "ConnectedThread: Starting");

        mySocket = socket;
        InputStream tempIn = null;
        OutputStream tempOut = null;


        try {
            tempIn = mySocket.getInputStream();
            tempOut = mySocket.getOutputStream();
        } catch (IOException e) {
            e.printStackTrace();
        }
        myInputStream = tempIn;
        myOutPutStream = tempOut;


        // Buffer store for the stream
        byte[] buffer = new byte[1024];

        // Bytes returned from the read()
        int bytes;

        while (true) {
            // Read from the InputStream
            try {
                bytes = myInputStream.read(buffer);
                String incomingMessage = new String(buffer, 0, bytes);
                Log.d(TAG2, "InputStream: " + incomingMessage);

                // Broadcast Incoming Message
                Intent incomingMsgIntent = new Intent("IncomingMsg");
                incomingMsgIntent.putExtra("receivingMsg", incomingMessage);
                LocalBroadcastManager.getInstance(myContext).sendBroadcast(incomingMsgIntent);


            } catch (IOException e) {

                // Broadcast Connection Message
                Intent connectionStatusIntent = new Intent("btConnectionStatus");
                connectionStatusIntent.putExtra("ConnectionStatus", "disconnect");
                connectionStatusIntent.putExtra("Device", myBtConnectionDevice);
                LocalBroadcastManager.getInstance(myContext).sendBroadcast(connectionStatusIntent);

                Log.d(TAG2, "CHAT SERVICE: Closed!!!");
                e.printStackTrace();
                break;

            } catch (Exception e){
                Log.d(TAG2, "CHAT SERVICE: Closed 2!!!: "+ e);
                e.printStackTrace();

            }


        }
    }


    // To write outgoing bluetooth messages
    public static void write(byte[] bytes) {

        String text = new String(bytes, Charset.defaultCharset());
        Log.d(TAG2, "Write: Writing to outputstream: " + text);

        try {
            myOutPutStream.write(bytes);
            myOutPutStream.flush();
        } catch (Exception e) {
            Log.d(TAG2, "Write: Error writing to output stream: " + e.getMessage());
        }
    }


    // To shut down bluetooth connection
    public void cancel() {
        try {
            mySocket.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }



    // To start Communication
    static void connected(BluetoothSocket mySocket, BluetoothDevice myDevice, Context context) {
        Log.d(TAG2, "Connected: Starting");


        myBtConnectionDevice = myDevice;
        myContext = context;
        //Start thread to manage the connection and perform transmissions
        startComms(mySocket);


    }

    /*
        Write to ConnectedThread in an unsynchronised manner
    */
    public static void writeMsg(byte[] out) {

        Log.d(TAG2, "write: Write Called.");
        write(out);

    }




}

