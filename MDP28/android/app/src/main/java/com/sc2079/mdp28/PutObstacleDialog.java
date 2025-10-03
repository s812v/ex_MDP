package com.sc2079.mdp28;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;

import androidx.annotation.Nullable;
import androidx.fragment.app.DialogFragment;

public class PutObstacleDialog extends DialogFragment {
    public View onCreateView(LayoutInflater inflater, @Nullable ViewGroup container, Bundle savedInstanceState) {
        View view = inflater.inflate(R.layout.put_obstacle, container, false);

        EditText obstacleNum = view.findViewById(R.id.obsnum);
        EditText obstacleX = view.findViewById(R.id.obsx);
        EditText obstacleY = view.findViewById(R.id.obsy);

        Button setObstacleBtn = view.findViewById(R.id.setOBButton);

        // Set a click listener for the Apply button
        setObstacleBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                // Get the values from the input fields
                String aValue = obstacleNum.getText().toString();
                String xValue = obstacleX.getText().toString();
                String yValue = obstacleY.getText().toString();

                // Send these values back to the calling fragment
                if (getTargetFragment() instanceof ArenaFragment) {
                    ((ArenaFragment) getTargetFragment()).applyValues(aValue, xValue, yValue, "180");
                }

                // Dismiss the dialog
                dismiss();
            }
        });

        return view;
    }

}
