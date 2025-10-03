/* USER CODE BEGIN Header */
/**
 ******************************************************************************
 * @file           : main.c
 * @brief          : Main program body
 ******************************************************************************
 * @attention
 *
 * Copyright (c) 2023 STMicroelectronics.
 * All rights reserved.
 *
 * This software is licensed under terms that can be found in the LICENSE file
 * in the root directory of this software component.
 * If no LICENSE file comes with this software, it is provided AS-IS.
 *
 ******************************************************************************
 */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "cmsis_os.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define SERVOCENTER 149
#define SERVORIGHT 210
#define SERVOLEFT 105
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
ADC_HandleTypeDef hadc1;
ADC_HandleTypeDef hadc2;

I2C_HandleTypeDef hi2c1;

TIM_HandleTypeDef htim1;
TIM_HandleTypeDef htim2;
TIM_HandleTypeDef htim3;
TIM_HandleTypeDef htim4;
TIM_HandleTypeDef htim8;

UART_HandleTypeDef huart3;

/* Definitions for defaultTask */
osThreadId_t defaultTaskHandle;
const osThreadAttr_t defaultTask_attributes = {
  .name = "defaultTask",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityNormal,
};
/* Definitions for motorTask */
osThreadId_t motorTaskHandle;
const osThreadAttr_t motorTask_attributes = {
  .name = "motorTask",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for OLEDTask */
osThreadId_t OLEDTaskHandle;
const osThreadAttr_t OLEDTask_attributes = {
  .name = "OLEDTask",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for gyroTask */
osThreadId_t gyroTaskHandle;
const osThreadAttr_t gyroTask_attributes = {
  .name = "gyroTask",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for ultrasonicTask */
osThreadId_t ultrasonicTaskHandle;
const osThreadAttr_t ultrasonicTask_attributes = {
  .name = "ultrasonicTask",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for communicateTask */
osThreadId_t communicateTaskHandle;
const osThreadAttr_t communicateTask_attributes = {
  .name = "communicateTask",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for encoderRTask */
osThreadId_t encoderRTaskHandle;
const osThreadAttr_t encoderRTask_attributes = {
  .name = "encoderRTask",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for encoderLTask */
osThreadId_t encoderLTaskHandle;
const osThreadAttr_t encoderLTask_attributes = {
  .name = "encoderLTask",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for Task2Handle */
osThreadId_t Task2HandleHandle;
const osThreadAttr_t Task2Handle_attributes = {
  .name = "Task2Handle",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityLow,
};
/* Definitions for IRTaskHandle */
osThreadId_t IRTaskHandleHandle;
const osThreadAttr_t IRTaskHandle_attributes = {
  .name = "IRTaskHandle",
  .stack_size = 128 * 4,
  .priority = (osPriority_t) osPriorityLow,
};
/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_I2C1_Init(void);
static void MX_TIM1_Init(void);
static void MX_TIM2_Init(void);
static void MX_TIM3_Init(void);
static void MX_TIM4_Init(void);
static void MX_TIM8_Init(void);
static void MX_USART3_UART_Init(void);
static void MX_ADC1_Init(void);
static void MX_ADC2_Init(void);
void StartDefaultTask(void *argument);
void StartMotorTask(void *argument);
void StartOLEDTask(void *argument);
void StartGyroTask(void *argument);
void StartUltrasonicTask(void *argument);
void StartCommunicateTask(void *argument);
void StartEncoderRTask(void *argument);
void StartEncoderLTask(void *argument);
void StartTask2(void *argument);
void StartIRTask(void *argument);

/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
// communication
uint8_t aRxBuffer[5] = { 0 };
int flagDone = 0;
int magnitude = 0;
int start =0;
char databuffer[20];
double sendback;

// movement
uint16_t pwmVal_servo = SERVOCENTER;
uint16_t pwmVal_R = 0;
uint16_t pwmVal_L = 0;
int control = 0;
int control2 = 0;
int control3 = 0;
volatile int times_acceptable = 0;
int e_brake = 0;
int extraNudge = 0;
int errorcorrection = 0;
int straightUS = 0;

// encoder
int32_t rightEncoderVal = 0, leftEncoderVal = 0;
int32_t rightTarget = 0, leftTarget = 0;
double target_angle = 0;

// gyro
double total_angle = 0;
uint8_t gyroBuffer[20];
uint8_t ICMAddress = 0x68;
double error_angle = 0;

// ultrasonic
int Is_First_Captured = 0;
int32_t IC_Val1 = 0;
int32_t IC_Val2 = 0;
uint16_t Difference = 0;
uint16_t Distance = 0;
uint16_t firstDistance = -1;
int k=0;

//task 2 Juke functions
int activateJuke=0;
int scan=0;
int turnDone=0;
int straightDone=0;
int travel = 0;
char nexttask = '8';
int turn90 = 0;
int movebackL=0;
int movebackR=0;
int usTargetGLOBAL = 28;
double universalDistance = 0;
int moveBackLeftRun1 = 0;
int moveBackRightRun1 = 0;
int moveBackLeftRun2 = 0;
int moveBackRightRun2 = 0;
int obsTwoLength = 0;
int obsTwoFlag = 0;

float voltage1, voltage2 = 0;
int irDistance1, irDistance2 = 0;
uint32_t ADC_VAL1,ADC_VAL2 = 0;

int main(void)
{
	/* Reset of all peripherals, Initializes the Flash interface and the Systick. */
	HAL_Init();
	SystemClock_Config();
	MX_GPIO_Init();
	MX_I2C1_Init();
	MX_TIM1_Init();
	MX_TIM2_Init();
	MX_TIM3_Init();
	MX_TIM4_Init();
	MX_TIM8_Init();
	MX_USART3_UART_Init();
	MX_ADC1_Init();
	MX_ADC2_Init();
	/* USER CODE BEGIN 2 */
	OLED_Init();
	HAL_UART_Receive_IT(&huart3, (uint8_t*) aRxBuffer, 5);
	/* USER CODE END 2 */

	/* Init scheduler */
	osKernelInitialize();
	defaultTaskHandle = osThreadNew(StartDefaultTask, NULL, &defaultTask_attributes);
	/* creation of motorTask */
	motorTaskHandle = osThreadNew(StartMotorTask, NULL, &motorTask_attributes);
	/* creation of OLEDTask */
	OLEDTaskHandle = osThreadNew(StartOLEDTask, NULL, &OLEDTask_attributes);
	/* creation of gyroTask */
	gyroTaskHandle = osThreadNew(StartGyroTask, NULL, &gyroTask_attributes);
	/* creation of ultrasonicTask */
	ultrasonicTaskHandle = osThreadNew(StartUltrasonicTask, NULL, &ultrasonicTask_attributes);
	/* creation of communicateTask */
	communicateTaskHandle = osThreadNew(StartCommunicateTask, NULL, &communicateTask_attributes);
	/* creation of encoderRTask */
	encoderRTaskHandle = osThreadNew(StartEncoderRTask, NULL, &encoderRTask_attributes);
	/* creation of encoderLTask */
	encoderLTaskHandle = osThreadNew(StartEncoderLTask, NULL, &encoderLTask_attributes);
	/* creation of Task2Handle */
	Task2HandleHandle = osThreadNew(StartTask2, NULL, &Task2Handle_attributes);
	/* creation of IRTaskHandle */
	IRTaskHandleHandle = osThreadNew(StartIRTask, NULL, &IRTaskHandle_attributes);
	osKernelStart();
	while (1) {

	}
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief ADC1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_ADC1_Init(void)
{

  /* USER CODE BEGIN ADC1_Init 0 */

  /* USER CODE END ADC1_Init 0 */

  ADC_ChannelConfTypeDef sConfig = {0};

  /* USER CODE BEGIN ADC1_Init 1 */

  /* USER CODE END ADC1_Init 1 */

  /** Configure the global features of the ADC (Clock, Resolution, Data Alignment and number of conversion)
  */
  hadc1.Instance = ADC1;
  hadc1.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV2;
  hadc1.Init.Resolution = ADC_RESOLUTION_12B;
  hadc1.Init.ScanConvMode = DISABLE;
  hadc1.Init.ContinuousConvMode = DISABLE;
  hadc1.Init.DiscontinuousConvMode = DISABLE;
  hadc1.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
  hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
  hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
  hadc1.Init.NbrOfConversion = 1;
  hadc1.Init.DMAContinuousRequests = DISABLE;
  hadc1.Init.EOCSelection = ADC_EOC_SINGLE_CONV;
  if (HAL_ADC_Init(&hadc1) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure for the selected ADC regular channel its corresponding rank in the sequencer and its sample time.
  */
  sConfig.Channel = ADC_CHANNEL_11;
  sConfig.Rank = 1;
  sConfig.SamplingTime = ADC_SAMPLETIME_3CYCLES;
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN ADC1_Init 2 */

  /* USER CODE END ADC1_Init 2 */

}

/**
  * @brief ADC2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_ADC2_Init(void)
{

  /* USER CODE BEGIN ADC2_Init 0 */

  /* USER CODE END ADC2_Init 0 */

  ADC_ChannelConfTypeDef sConfig = {0};

  /* USER CODE BEGIN ADC2_Init 1 */

  /* USER CODE END ADC2_Init 1 */

  /** Configure the global features of the ADC (Clock, Resolution, Data Alignment and number of conversion)
  */
  hadc2.Instance = ADC2;
  hadc2.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV2;
  hadc2.Init.Resolution = ADC_RESOLUTION_12B;
  hadc2.Init.ScanConvMode = DISABLE;
  hadc2.Init.ContinuousConvMode = DISABLE;
  hadc2.Init.DiscontinuousConvMode = DISABLE;
  hadc2.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
  hadc2.Init.ExternalTrigConv = ADC_SOFTWARE_START;
  hadc2.Init.DataAlign = ADC_DATAALIGN_RIGHT;
  hadc2.Init.NbrOfConversion = 1;
  hadc2.Init.DMAContinuousRequests = DISABLE;
  hadc2.Init.EOCSelection = ADC_EOC_SINGLE_CONV;
  if (HAL_ADC_Init(&hadc2) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure for the selected ADC regular channel its corresponding rank in the sequencer and its sample time.
  */
  sConfig.Channel = ADC_CHANNEL_12;
  sConfig.Rank = 1;
  sConfig.SamplingTime = ADC_SAMPLETIME_3CYCLES;
  if (HAL_ADC_ConfigChannel(&hadc2, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief I2C1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_I2C1_Init(void)
{
  hi2c1.Instance = I2C1;
  hi2c1.Init.ClockSpeed = 100000;
  hi2c1.Init.DutyCycle = I2C_DUTYCYCLE_2;
  hi2c1.Init.OwnAddress1 = 0;
  hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c1.Init.OwnAddress2 = 0;
  hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
  if (HAL_I2C_Init(&hi2c1) != HAL_OK)
  {
    Error_Handler();
  }
}

static void MX_TIM1_Init(void)
{

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};
  TIM_BreakDeadTimeConfigTypeDef sBreakDeadTimeConfig = {0};
  htim1.Instance = TIM1;
  htim1.Init.Prescaler = 160;
  htim1.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim1.Init.Period = 1000;
  htim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim1.Init.RepetitionCounter = 0;
  htim1.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
  if (HAL_TIM_Base_Init(&htim1) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim1, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_Init(&htim1) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim1, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  sConfigOC.OCIdleState = TIM_OCIDLESTATE_RESET;
  sConfigOC.OCNIdleState = TIM_OCNIDLESTATE_RESET;
  if (HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_4) != HAL_OK)
  {
    Error_Handler();
  }
  sBreakDeadTimeConfig.OffStateRunMode = TIM_OSSR_DISABLE;
  sBreakDeadTimeConfig.OffStateIDLEMode = TIM_OSSI_DISABLE;
  sBreakDeadTimeConfig.LockLevel = TIM_LOCKLEVEL_OFF;
  sBreakDeadTimeConfig.DeadTime = 0;
  sBreakDeadTimeConfig.BreakState = TIM_BREAK_DISABLE;
  sBreakDeadTimeConfig.BreakPolarity = TIM_BREAKPOLARITY_HIGH;
  sBreakDeadTimeConfig.AutomaticOutput = TIM_AUTOMATICOUTPUT_DISABLE;
  if (HAL_TIMEx_ConfigBreakDeadTime(&htim1, &sBreakDeadTimeConfig) != HAL_OK)
  {
    Error_Handler();
  }
  HAL_TIM_MspPostInit(&htim1);
}

// ! @brief TIM2 Initialization Function
static void MX_TIM2_Init(void)
{
  TIM_Encoder_InitTypeDef sConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};
  htim2.Instance = TIM2;
  htim2.Init.Prescaler = 0;
  htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim2.Init.Period = 65535;
  htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  sConfig.EncoderMode = TIM_ENCODERMODE_TI12;
  sConfig.IC1Polarity = TIM_ICPOLARITY_RISING;
  sConfig.IC1Selection = TIM_ICSELECTION_DIRECTTI;
  sConfig.IC1Prescaler = TIM_ICPSC_DIV1;
  sConfig.IC1Filter = 10;
  sConfig.IC2Polarity = TIM_ICPOLARITY_RISING;
  sConfig.IC2Selection = TIM_ICSELECTION_DIRECTTI;
  sConfig.IC2Prescaler = TIM_ICPSC_DIV1;
  sConfig.IC2Filter = 10;
  if (HAL_TIM_Encoder_Init(&htim2, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim2, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
}

// ! @brief TIM3 Initialization Function
static void MX_TIM3_Init(void)
{
  TIM_Encoder_InitTypeDef sConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};
  htim3.Instance = TIM3;
  htim3.Init.Prescaler = 0;
  htim3.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim3.Init.Period = 65535;
  htim3.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim3.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  sConfig.EncoderMode = TIM_ENCODERMODE_TI12;
  sConfig.IC1Polarity = TIM_ICPOLARITY_RISING;
  sConfig.IC1Selection = TIM_ICSELECTION_DIRECTTI;
  sConfig.IC1Prescaler = TIM_ICPSC_DIV1;
  sConfig.IC1Filter = 10;
  sConfig.IC2Polarity = TIM_ICPOLARITY_RISING;
  sConfig.IC2Selection = TIM_ICSELECTION_DIRECTTI;
  sConfig.IC2Prescaler = TIM_ICPSC_DIV1;
  sConfig.IC2Filter = 10;
  if (HAL_TIM_Encoder_Init(&htim3, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim3, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
}

// ! @brief TIM4 Initialization Function
static void MX_TIM4_Init(void)
{
  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_IC_InitTypeDef sConfigIC = {0};

  htim4.Instance = TIM4;
  htim4.Init.Prescaler = 16;
  htim4.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim4.Init.Period = 65535;
  htim4.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim4.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_IC_Init(&htim4) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim4, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigIC.ICPolarity = TIM_INPUTCHANNELPOLARITY_RISING;
  sConfigIC.ICSelection = TIM_ICSELECTION_DIRECTTI;
  sConfigIC.ICPrescaler = TIM_ICPSC_DIV1;
  sConfigIC.ICFilter = 0;
  if (HAL_TIM_IC_ConfigChannel(&htim4, &sConfigIC, TIM_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
}

//! @brief TIM8 Initialization Function
static void MX_TIM8_Init(void)
{
  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};
  TIM_BreakDeadTimeConfigTypeDef sBreakDeadTimeConfig = {0};
  htim8.Instance = TIM8;
  htim8.Init.Prescaler = 0;
  htim8.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim8.Init.Period = 7199;
  htim8.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim8.Init.RepetitionCounter = 0;
  htim8.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim8) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim8, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_Init(&htim8) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim8, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCNPolarity = TIM_OCNPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  sConfigOC.OCIdleState = TIM_OCIDLESTATE_RESET;
  sConfigOC.OCNIdleState = TIM_OCNIDLESTATE_RESET;
  if (HAL_TIM_PWM_ConfigChannel(&htim8, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim8, &sConfigOC, TIM_CHANNEL_2) != HAL_OK)
  {
    Error_Handler();
  }
  sBreakDeadTimeConfig.OffStateRunMode = TIM_OSSR_DISABLE;
  sBreakDeadTimeConfig.OffStateIDLEMode = TIM_OSSI_DISABLE;
  sBreakDeadTimeConfig.LockLevel = TIM_LOCKLEVEL_OFF;
  sBreakDeadTimeConfig.DeadTime = 0;
  sBreakDeadTimeConfig.BreakState = TIM_BREAK_DISABLE;
  sBreakDeadTimeConfig.BreakPolarity = TIM_BREAKPOLARITY_HIGH;
  sBreakDeadTimeConfig.AutomaticOutput = TIM_AUTOMATICOUTPUT_DISABLE;
  if (HAL_TIMEx_ConfigBreakDeadTime(&htim8, &sBreakDeadTimeConfig) != HAL_OK)
  {
    Error_Handler();
  }
}

// ! @brief USART3 Initialization Function
static void MX_USART3_UART_Init(void)
{
  huart3.Instance = USART3;
  huart3.Init.BaudRate = 115200;
  huart3.Init.WordLength = UART_WORDLENGTH_8B;
  huart3.Init.StopBits = UART_STOPBITS_1;
  huart3.Init.Parity = UART_PARITY_NONE;
  huart3.Init.Mode = UART_MODE_TX_RX;
  huart3.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart3.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart3) != HAL_OK)
  {
    Error_Handler();
  }
}

// ! @brief GPIO Initialization Function
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
/* USER CODE BEGIN MX_GPIO_Init_1 */
/* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOE_CLK_ENABLE();
  __HAL_RCC_GPIOH_CLK_ENABLE();
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOE, OLED_SCL_Pin|OLED_SDA_Pin|OLED_RST_Pin|OLED_DC_Pin
                          |LED3_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOA, AIN2_Pin|AIN1_Pin|BIN1_Pin|BIN2_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(Buzzer_GPIO_Port, Buzzer_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(Trigger_GPIO_Port, Trigger_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pins : OLED_SCL_Pin OLED_SDA_Pin OLED_RST_Pin OLED_DC_Pin
                           LED3_Pin */
  GPIO_InitStruct.Pin = OLED_SCL_Pin|OLED_SDA_Pin|OLED_RST_Pin|OLED_DC_Pin
                          |LED3_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOE, &GPIO_InitStruct);

  /*Configure GPIO pins : AIN2_Pin AIN1_Pin BIN1_Pin BIN2_Pin */
  GPIO_InitStruct.Pin = AIN2_Pin|AIN1_Pin|BIN1_Pin|BIN2_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pin : Buzzer_Pin */
  GPIO_InitStruct.Pin = Buzzer_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(Buzzer_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : USER_PB_Pin */
  GPIO_InitStruct.Pin = USER_PB_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_RISING;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(USER_PB_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : Trigger_Pin */
  GPIO_InitStruct.Pin = Trigger_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(Trigger_GPIO_Port, &GPIO_InitStruct);

/* USER CODE BEGIN MX_GPIO_Init_2 */
/* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */
// communication
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
	/* to prevent unused argument(s) compilation warning */
	UNUSED(huart);
	HAL_UART_Receive_IT(&huart3, aRxBuffer, 5);
}
void HAL_GPIO_EXTI_Callback( uint16_t GPIO_Pin ) {
	if (GPIO_Pin == USER_PB_Pin) {
		if (start == 0){
			start = 1;
		    }
		else
			start = 0;
 	    }
}

// ultrasonic
void delay(uint16_t time) {
	__HAL_TIM_SET_COUNTER(&htim4, 0);
	while (__HAL_TIM_GET_COUNTER (&htim4) < time)
		;
}

void HAL_TIM_IC_CaptureCallback(TIM_HandleTypeDef *htim) {
	if (htim->Channel == HAL_TIM_ACTIVE_CHANNEL_1) {
		if (Is_First_Captured == 0) {
			IC_Val1 = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_1);
			Is_First_Captured = 1;
			__HAL_TIM_SET_CAPTUREPOLARITY(htim, TIM_CHANNEL_1,
					TIM_INPUTCHANNELPOLARITY_FALLING);
		} else if (Is_First_Captured == 1) {
			IC_Val2 = HAL_TIM_ReadCapturedValue(htim, TIM_CHANNEL_1);
			__HAL_TIM_SET_COUNTER(htim, 0);

			if (IC_Val2 > IC_Val1) {
				Difference = IC_Val2 - IC_Val1;
			}

			else if (IC_Val1 > IC_Val2) {
				Difference = (65535 - IC_Val1) + IC_Val2;
			}

			Distance = Difference * .0343 / 2;

			Is_First_Captured = 0;

			__HAL_TIM_SET_CAPTUREPOLARITY(htim, TIM_CHANNEL_1,
					TIM_INPUTCHANNELPOLARITY_RISING);
			__HAL_TIM_DISABLE_IT(&htim4, TIM_IT_CC1);
		}
	}
}

void HCSR04_Read(void) //Call when u want to get reading from US
{
	HAL_GPIO_WritePin(Trigger_GPIO_Port, Trigger_Pin, GPIO_PIN_SET);
	delay(10);
	HAL_GPIO_WritePin(Trigger_GPIO_Port, Trigger_Pin, GPIO_PIN_RESET);
	__HAL_TIM_ENABLE_IT(&htim4, TIM_IT_CC1);
}
//task 2 funct

// movement
void moveCarStraight(double distance) {
	distance = distance * 75 * 0.99;
	pwmVal_servo = SERVOCENTER;
	osDelay(300);
	e_brake = 0;
	times_acceptable = 0;
	rightEncoderVal = 75000;
	leftEncoderVal = 75000;
	rightTarget = 75000;
	leftTarget = 75000;
	rightTarget += distance;
	leftTarget += distance;
	control =0;
	//while (finishCheck2());

}


void buzzerBeep()
{
	HAL_GPIO_TogglePin(GPIOB, GPIO_PIN_10); //Buzzer On
	HAL_Delay(1000);
	HAL_GPIO_TogglePin(GPIOB, GPIO_PIN_10); //Buzzer Off
}

void moveCarStop() {
	e_brake = 1;
	pwmVal_servo = SERVOCENTER;
	osDelay(300);
}

void moveCarRight(double angle) {
	pwmVal_servo = SERVORIGHT;
	osDelay(200);
	e_brake = 0;
	control = 1;
	times_acceptable = 0;
	target_angle -= angle;
	while (finishCheck2());
}

void moveCarRightFaster(double angle) {
	pwmVal_servo = SERVORIGHT;
	osDelay(100);
	e_brake = 0;
	control = 1;
	times_acceptable = 0;
	target_angle -= angle;
	while (finishCheck2());
}

void moveCarLeftFaster(double angle) {
	pwmVal_servo = SERVOLEFT;
	osDelay(100);
	e_brake = 0;
	control = 1;
	times_acceptable = 0;
	target_angle += angle;
	while (finishCheck2());
}

void moveCarLeft(double angle) {
	pwmVal_servo = SERVOLEFT;
	osDelay(300);
	e_brake = 0;
	control = 1;
	times_acceptable = 0;
	target_angle += angle;
	while (finishCheck2());
}

// error correction
int PID_Control(int error, int right) {//straights
	if (right) { //rightMotor
		if (error > 0) { //go forward
			HAL_GPIO_WritePin(GPIOA, BIN1_Pin, GPIO_PIN_SET); // set direction of rotation for wheel B- forward
			HAL_GPIO_WritePin(GPIOA, BIN2_Pin, GPIO_PIN_RESET);
		} else { //go backward
			HAL_GPIO_WritePin(GPIOA, BIN1_Pin, GPIO_PIN_RESET); // set direction of rotation for wheel B - reverse
			HAL_GPIO_WritePin(GPIOA, BIN2_Pin, GPIO_PIN_SET);
		}
	} else { //leftMotor
		if (error > 0) { //go forward
			HAL_GPIO_WritePin(GPIOA, AIN1_Pin, GPIO_PIN_SET); // set direction of rotation for wheel A - forward
			HAL_GPIO_WritePin(GPIOA, AIN2_Pin, GPIO_PIN_RESET);
		} else { //go backward
			HAL_GPIO_WritePin(GPIOA, AIN1_Pin, GPIO_PIN_RESET); // set direction of rotation for wheel A - reverse
			HAL_GPIO_WritePin(GPIOA, AIN2_Pin, GPIO_PIN_SET);
		}
	}
	error = abs(error);
	if (error > 2000) {
		return 4000; // 3000
	} else if (error > 500) {
		return 3000; // 2500
	} else if (error > 200) {
		return 2500; // 1700
	} else if (error > 100) {
		return 1500; // 1000
	} else if (error > 2) {
		times_acceptable++;
		return 700;
	} else if (error >= 1) {
		times_acceptable++;
		return 0;
	} else {
		times_acceptable++;
		return 0;
	}
}
int PID_Juke(double error, int right)//ultrasonic
{
	//int outputPWM = 0;
	int temp = 1;

	//degree of acceptance will be 28-28.5, 40?  //10

	if (error < usTargetGLOBAL){
		error = usTargetGLOBAL*2 - error ;
		temp = -1;
	}


	if(right){//rightMotor
		if(temp>0){//go forward
			HAL_GPIO_WritePin(GPIOA, BIN1_Pin, GPIO_PIN_SET); // set direction of rotation for wheel B- forward
			HAL_GPIO_WritePin(GPIOA, BIN2_Pin, GPIO_PIN_RESET);
		}else{//go backward
		    HAL_GPIO_WritePin(GPIOA, BIN1_Pin, GPIO_PIN_RESET); // set direction of rotation for wheel B - reverse
			HAL_GPIO_WritePin(GPIOA, BIN2_Pin, GPIO_PIN_SET);
		}
	}else{//leftMotor
		if(temp>0){//go forward
			HAL_GPIO_WritePin(GPIOA, AIN1_Pin, GPIO_PIN_SET); // set direction of rotation for wheel A - forward
			HAL_GPIO_WritePin(GPIOA, AIN2_Pin, GPIO_PIN_RESET);
		}else{//go backward
		    HAL_GPIO_WritePin(GPIOA, AIN1_Pin, GPIO_PIN_RESET); // set direction of rotation for wheel A - reverse
			HAL_GPIO_WritePin(GPIOA, AIN2_Pin, GPIO_PIN_SET);
		}
	}

	if(error<0){
		error *= -1;
	}

	if(error > 40){
		return 4000; // 4000
	}else if(error > usTargetGLOBAL+9){
		return 3500; // 3300
	}else if(error > usTargetGLOBAL+5){
		return 1500; //900
	}
	else if(error > usTargetGLOBAL+3){
			times_acceptable++; // there is None here
			return 900; //900
	}else if(error <=usTargetGLOBAL+.5){
		times_acceptable++;
		return 0;
	}else{
		times_acceptable +=500;; //500
		return 0;
	}


}

int PID_Angle(double errord, int right) {
	int error = (int) (errord * 10);
	if (right) { //rightMotor
		if (error > 0) { //go forward
			HAL_GPIO_WritePin(GPIOA, BIN1_Pin, GPIO_PIN_SET); // set direction of rotation for wheel B- forward
			HAL_GPIO_WritePin(GPIOA, BIN2_Pin, GPIO_PIN_RESET);
		} else { //go backward
			HAL_GPIO_WritePin(GPIOA, BIN1_Pin, GPIO_PIN_RESET); // set direction of rotation for wheel B - reverse
			HAL_GPIO_WritePin(GPIOA, BIN2_Pin, GPIO_PIN_SET);
		}
	} else { //leftMotor
		if (error < 0) { //go forward
			HAL_GPIO_WritePin(GPIOA, AIN1_Pin, GPIO_PIN_SET); // set direction of rotation for wheel A - forward
			HAL_GPIO_WritePin(GPIOA, AIN2_Pin, GPIO_PIN_RESET);
		} else { //go backward
			HAL_GPIO_WritePin(GPIOA, AIN1_Pin, GPIO_PIN_RESET); // set direction of rotation for wheel A - reverse
			HAL_GPIO_WritePin(GPIOA, AIN2_Pin, GPIO_PIN_SET);
		}
	}

	error = abs(error);
	if (error > 1000){
		return 6000; // new add
	}else if (error > 700) {
		return 5500;
	}else if (error > 300) {
		return 3600; // 3300
	} else if (error > 200) {
		return 3200; // 3000
	} else if (error > 150) {
		return 3000; // 2400
	} else if (error > 100) {
		return 2600; // 2000
	}else if (error > 70) {
//		times_acceptable++;
		return 1500;
	} else if (error > 50) {
		times_acceptable++;
		return 1000; // 1000
	} else if (error >= 25) {
		times_acceptable++;
		return 900; // 1000
	} else if (error >= 8) {
		times_acceptable++;
		return 800;
	} else {
		times_acceptable++;
		return 200; // 200
	}
}

int finishCheck() {
	if (times_acceptable > 20) {
		e_brake = 1;
		pwmVal_L = pwmVal_R = 0;
		leftTarget = leftEncoderVal;
		rightTarget = rightEncoderVal;
		times_acceptable = 0;
		straightUS = 0;
		errorcorrection = 0;
		control = 0;
		osDelay(30);

		return 0;
	}
	return 1;
}
int finishCheck2() {
	if (times_acceptable > 8) { // 5

		return 0;
	}
	return 1;
}

void finished() {
		e_brake = 1;
		pwmVal_L = pwmVal_R = 0;
		leftTarget = leftEncoderVal;
		rightTarget = rightEncoderVal;
		times_acceptable = 0;
		control = 0;
		control2 = 0;
		control3 = 0;
		straightUS = 0;
		osDelay(30);

}

void IRCheck(int a){
	pwmVal_servo = a;
	osDelay(30);
	e_brake = 0;
	control = 1;
}

// gyro
void readByte(uint8_t addr, uint8_t *data) {
	gyroBuffer[0] = addr;
	HAL_I2C_Master_Transmit(&hi2c1, ICMAddress << 1, gyroBuffer, 1, 10);
	HAL_I2C_Master_Receive(&hi2c1, ICMAddress << 1, data, 2, 20);
}

void writeByte(uint8_t addr, uint8_t data) {
	gyroBuffer[0] = addr;
	gyroBuffer[1] = data;
	HAL_I2C_Master_Transmit(&hi2c1, ICMAddress << 1, gyroBuffer, 2, 20);
}

void gyroInit() {
	writeByte(0x06, 0x00);
	osDelay(10);
	writeByte(0x03, 0x80);
	osDelay(10);
	writeByte(0x07, 0x07);
	osDelay(10);
	writeByte(0x06, 0x01);
	osDelay(10);
	writeByte(0x7F, 0x20);
	osDelay(10);
	writeByte(0x01, 0x2F);
	osDelay(10);
	writeByte(0x0, 0x00);
	osDelay(10);
	writeByte(0x7F, 0x00);
	osDelay(10);
	writeByte(0x07, 0x00);
	osDelay(10);
}

void StartDefaultTask(void *argument)
{
  /* USER CODE BEGIN 5 */
	/* Infinite loop */
	for (;;) {
		HAL_GPIO_TogglePin(LED3_GPIO_Port, LED3_Pin);
		osDelay(2000);
	}
  /* USER CODE END 5 */
}

void StartMotorTask(void *argument)
{
	//control = 1 gives free rein over the servo direction
  /* USER CODE BEGIN StartMotorTask */
	pwmVal_R = 0;
	pwmVal_L = 0;
	int straightCorrection = 0;
	HAL_TIM_PWM_Start(&htim8, TIM_CHANNEL_1);
	HAL_TIM_PWM_Start(&htim8, TIM_CHANNEL_2);
	HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_4);
	htim1.Instance->CCR4 = SERVOCENTER; //Centre


	osDelay(300);


	/* Infinite loop */
	for (;;) {
		htim1.Instance->CCR4 = pwmVal_servo;
		error_angle = target_angle - total_angle;
		if(control == 1){
			if (pwmVal_servo < 127) { //106 //TURN LEFT
				//gyroCheck = PID_Angle(error_angle, 1);
				pwmVal_R = PID_Angle(error_angle, 1);  //right is master
				pwmVal_L = pwmVal_R * (0.33); //left is slave
				HAL_GPIO_WritePin(GPIOA, AIN1_Pin, GPIO_PIN_SET); // set direction of rotation for wheel A- reverse
				HAL_GPIO_WritePin(GPIOA, AIN2_Pin, GPIO_PIN_RESET);
				HAL_GPIO_WritePin(GPIOA, BIN2_Pin, GPIO_PIN_RESET); // set direction of rotation for wheel B - Forward
				HAL_GPIO_WritePin(GPIOA, BIN1_Pin, GPIO_PIN_SET);
			} else if (pwmVal_servo > 189) { //230 //TURN RIGHT
				//gyroCheck = PID_Angle(error_angle, 0);
				pwmVal_L = PID_Angle(error_angle, 0);
				pwmVal_R = pwmVal_L * (0.37); //right is slave
				HAL_GPIO_WritePin(GPIOA, AIN1_Pin, GPIO_PIN_SET); // set direction of rotation for wheel A- reverse
				HAL_GPIO_WritePin(GPIOA, AIN2_Pin, GPIO_PIN_RESET);
				HAL_GPIO_WritePin(GPIOA, BIN2_Pin, GPIO_PIN_RESET); // set direction of rotation for wheel B - Forward
				HAL_GPIO_WritePin(GPIOA, BIN1_Pin, GPIO_PIN_SET);
			}
			else{
				if(control2 ==1 && control3 == 0){
					pwmVal_R = 4500; // 2600
					pwmVal_L = 4500; // 2600
				} else if (control2 == 1 && control3 == 1) {
					pwmVal_R = 3000; // 2600
					pwmVal_L = 3000; // 2600 run slight real slow
				}
				else{
					pwmVal_R = 5000; // 4000
					pwmVal_L = 5000; // 4000
				}
				HAL_GPIO_WritePin(GPIOA, AIN1_Pin, GPIO_PIN_SET); // set direction of rotation for wheel A- reverse
				HAL_GPIO_WritePin(GPIOA, AIN2_Pin, GPIO_PIN_RESET);
				HAL_GPIO_WritePin(GPIOA, BIN2_Pin, GPIO_PIN_RESET); // set direction of rotation for wheel B - Forward
				HAL_GPIO_WritePin(GPIOA, BIN1_Pin, GPIO_PIN_SET);
				if(errorcorrection == 1){
					if (error_angle>5){ // if turn left, 106. right 230. left +. right -.
						pwmVal_servo=((8*5)/5 + 150);
					}
					else if(error_angle<-5){
						pwmVal_servo=((-8*5)/5 + 150);
					}else{
						pwmVal_servo=((8*error_angle)/5 + 150);
					}
				}
			}

		}
		else{
			if (pwmVal_servo < 127) { //106 //TURN LEFT
				pwmVal_R = PID_Angle(error_angle, 1)*1.1;  //right is master
				pwmVal_L = pwmVal_R * (0.33); //left is slave

				if (error_angle > 0) {
					//go forward
					//pwmVal_L = pwmVal_R * (0.79); //left is slave
					HAL_GPIO_WritePin(GPIOA, AIN1_Pin, GPIO_PIN_SET); // set direction of rotation for wheel A- reverse
					HAL_GPIO_WritePin(GPIOA, AIN2_Pin, GPIO_PIN_RESET);
					HAL_GPIO_WritePin(GPIOA, BIN2_Pin, GPIO_PIN_RESET); // set direction of rotation for wheel B - Forward
					HAL_GPIO_WritePin(GPIOA, BIN1_Pin, GPIO_PIN_SET);
				} else {
					//go backward
					pwmVal_L = pwmVal_R * (0.49); //left is slave
					//pwmVal_servo = 106;
					HAL_GPIO_WritePin(GPIOA, AIN1_Pin, GPIO_PIN_RESET); // set direction of rotation for wheel A - forward
					HAL_GPIO_WritePin(GPIOA, AIN2_Pin, GPIO_PIN_SET);
					HAL_GPIO_WritePin(GPIOA, BIN2_Pin, GPIO_PIN_SET); // set direction of rotation for wheel B- reverse
					HAL_GPIO_WritePin(GPIOA, BIN1_Pin, GPIO_PIN_RESET);
				}
			} else if (pwmVal_servo > 189) { //230 //TURN RIGHT
				pwmVal_L = PID_Angle(error_angle, 0);
				pwmVal_R = pwmVal_L * (0.37); //right is slave

				if (error_angle < 0) {
					//go forward
					//pwmVal_R = pwmVal_L * (0.37); //right is slave
					HAL_GPIO_WritePin(GPIOA, BIN1_Pin, GPIO_PIN_SET); // set direction of rotation for wheel B- Reverse
					HAL_GPIO_WritePin(GPIOA, BIN2_Pin, GPIO_PIN_RESET);
					HAL_GPIO_WritePin(GPIOA, AIN2_Pin, GPIO_PIN_RESET); // set direction of rotation for wheel A - forward
					HAL_GPIO_WritePin(GPIOA, AIN1_Pin, GPIO_PIN_SET);
				} else {
					//go backward
					pwmVal_R = pwmVal_L * (0.305); //right is slave

					HAL_GPIO_WritePin(GPIOA, BIN1_Pin, GPIO_PIN_RESET); // set direction of rotation for wheel B - reverse
					HAL_GPIO_WritePin(GPIOA, BIN2_Pin, GPIO_PIN_SET);
					HAL_GPIO_WritePin(GPIOA, AIN2_Pin, GPIO_PIN_SET); // set direction of rotation for wheel A- forward
					HAL_GPIO_WritePin(GPIOA, AIN1_Pin, GPIO_PIN_RESET);
				}
			} else {
				if(straightUS) {
					pwmVal_L = PID_Juke(Distance, 1);
					if (abs(leftEncoderVal)<abs(rightEncoderVal)){
						straightCorrection++;
					} else{ straightCorrection--;}
					if (pwmVal_R<1000){
						straightCorrection=0;
					}
					pwmVal_R = PID_Juke(Distance, 0) + straightCorrection;

				}
				else {
					pwmVal_L = PID_Control(rightTarget - rightEncoderVal, 1);
					if (abs(leftEncoderVal)<abs(rightEncoderVal)){
						straightCorrection++;
					} else {
						straightCorrection--;
					}
					if (pwmVal_R<1000){
						straightCorrection=0;
					}
					pwmVal_R = PID_Control(leftTarget - leftEncoderVal, 0) + straightCorrection;
				}
				//line correction equation is pwmVal = (19*error)/5 + SERVOCENTER
				if (errorcorrection == 1){
					if(Distance>usTargetGLOBAL){
						if (error_angle>5){ // if turn left, 106. right 230. left +. right -.
							pwmVal_servo=((-8*5)/5 + 150);
						}
						else if(error_angle<-5){
							pwmVal_servo=((8*5)/5 + 150);
						}else{
							pwmVal_servo=((-8*error_angle)/5 + 150);
						}
					} else {
						if (error_angle>5){ // if turn left, 106. right 230. left +. right -.
							pwmVal_servo=((8*5)/5 + 150);
						}
						else if(error_angle<-5){
							pwmVal_servo=((-8*5)/5 + 150);
						}else{
							pwmVal_servo=((8*error_angle)/5 + 150);
						}
					}
				}
			}
		}

		if (e_brake) {
			pwmVal_L = pwmVal_R = 0;
			leftTarget = leftEncoderVal;
			rightTarget = rightEncoderVal;
		}

		__HAL_TIM_SetCompare(&htim8,TIM_CHANNEL_1,pwmVal_L);

		__HAL_TIM_SetCompare(&htim8,TIM_CHANNEL_2,(pwmVal_R * 1.15));
		osDelay(1);

		if (times_acceptable > 1000) {
			times_acceptable = 1001;
		}
	}
  /* USER CODE END StartMotorTask */
}

/* USER CODE BEGIN Header_StartOLEDTask */
/**
 * @brief Function implementing the OLEDTask thread.
 * @param argument: Not used
 * @retval None
 */
/* USER CODE END Header_StartOLEDTask */
void StartOLEDTask(void *argument)
{
  /* USER CODE BEGIN StartOLEDTask */
	uint8_t usVal[20] = { 0 };
	uint8_t gyroVal[20] = { 0 };
	uint8_t command[20] = { 0 };
	uint8_t lefty[20] = { 0 };
	uint8_t righty[20] = { 0 };
	for (;;) {
		sprintf(usVal, "Distance: %d \0", (int) Distance);
		OLED_ShowString(0, 10, usVal);

		int decimals = abs((int) ((total_angle - (int) (total_angle)) * 1000));
		sprintf(gyroVal, "TGyro: %d.%d \0", (int) total_angle, decimals);
		OLED_ShowString(0, 20, gyroVal);
		sprintf(lefty, "IRL: %d \0", irDistance1);
		OLED_ShowString(0, 30, lefty);
		sprintf(righty, "IRR: %d \0", irDistance2);
		OLED_ShowString(0, 40, righty);

		sprintf(command, "C: %c%c%c%c \0", aRxBuffer[0],aRxBuffer[1],aRxBuffer[2],aRxBuffer[3]);
		OLED_ShowString(0, 50, command);

		OLED_Refresh_Gram();
		osDelay(100);
	}
  /* USER CODE END StartOLEDTask */
}

/* USER CODE BEGIN Header_StartGyroTask */
/**
 * @brief Function implementing the gyroTask thread.
 * @param argument: Not used
 * @retval None
 */
/* USER CODE END Header_StartGyroTask */
void StartGyroTask(void *argument)
{
  /* USER CODE BEGIN StartGyroTask */
	gyroInit();
	uint8_t val[2] = { 0, 0 };

	int16_t angular_speed = 0;

	uint32_t tick = 0;
	double offset = 0;
	double trash = 0;
	int i = 0;
	while (i < 300) { // 300, reduce the calibration
		osDelay(30); // 50, reduce the sampling
		readByte(0x37, val);
		angular_speed = (val[0] << 8) | val[1];
		trash += (double) ((double) angular_speed)
				* ((HAL_GetTick() - tick) / 16400.0);
		offset += angular_speed;
		tick = HAL_GetTick();
		i++;
	}
	buzzerBeep();
	k = 1;
	offset = offset / i;

	tick = HAL_GetTick();
	/* Infinite loop */
	for (;;) {

		osDelay(10);
		if (HAL_GetTick() - tick >= 2) {
			readByte(0x37, val);
			angular_speed = (val[0] << 8) | val[1];
			total_angle += (double) ((double) angular_speed - offset)
					* ((HAL_GetTick() - tick) / 16400.0);
//			total_angle += (double) ((double) angular_speed / 16.4 * 0.01);
			i -= angular_speed;
			tick = HAL_GetTick();
			i++;
		}
	}
  /* USER CODE END StartGyroTask */
}

/* USER CODE BEGIN Header_StartUltrasonicTask */
/**
 * @brief Function implementing the ultrasonicTask thread.
 * @param argument: Not used
 * @retval None
 */
/* USER CODE END Header_StartUltrasonicTask */
void StartUltrasonicTask(void *argument)
{
  /* USER CODE BEGIN StartUltrasonicTask */
	HAL_TIM_IC_Start_IT(&htim4, TIM_CHANNEL_1);  // HC-SR04 Sensor
	osDelay(5000);
	/* Infinite loop */
	for (;;) {
		HCSR04_Read();
		osDelay(100);
	}
  /* USER CODE END StartUltrasonicTask */
}

/* USER CODE BEGIN Header_StartCommunicateTask */
/**
 * @brief Function implementing the communicateTask thread.
 * @param argument: Not used
 * @retval None
 */
/* USER CODE END Header_StartCommunicateTask */
void StartCommunicateTask(void *argument)
{
	char ack = 'A';
	int corr = 8;
	aRxBuffer[0] = 'E';
	aRxBuffer[1] = 'M';
	aRxBuffer[2] = 'P';
	aRxBuffer[3] = 'T';
	aRxBuffer[4] = 'Y';

	/* Infinite loop */
	for (;;) {
	}
}

/* USER CODE BEGIN Header_StartEncoderRTask */
/**
 * @brief Function implementing the encoderRTask thread.
 * @param argument: Not used
 * @retval None
 */
/* USER CODE END Header_StartEncoderRTask */
void StartEncoderRTask(void *argument)
{
  /* USER CODE BEGIN StartEncoderRTask */
	/* Infinite loop */
	HAL_TIM_Encoder_Start(&htim3, TIM_CHANNEL_ALL);
	int cnt1;
	int dirR = 1;
	int diff;
	uint32_t tick = HAL_GetTick();
	/* Infinite loop */
	for (;;) {
		if (HAL_GetTick() - tick > 10L) {
			cnt1 = __HAL_TIM_GET_COUNTER(&htim3);
			if (cnt1 > 32000) {
				dirR = 1;
				diff = (65536 - cnt1);
			} else {
				dirR = -1;
				diff = cnt1;
			}

			if (dirR == 1) {
				rightEncoderVal -= diff;
			} else {
				rightEncoderVal += diff;
			}

			__HAL_TIM_SET_COUNTER(&htim3, 0);

			tick = HAL_GetTick();
		}
	}
  /* USER CODE END StartEncoderRTask */
}

/* USER CODE BEGIN Header_StartEncoderLTask */
/**
 * @brief Function implementing the encoderLTask thread.
 * @param argument: Not used
 * @retval None
 */
/* USER CODE END Header_StartEncoderLTask */
void StartEncoderLTask(void *argument)
{
  /* USER CODE BEGIN StartEncoderLTask */
	HAL_TIM_Encoder_Start(&htim2, TIM_CHANNEL_ALL);
	int cnt2;
	int dirL = 1;
	int diff;
	uint32_t tick = HAL_GetTick();
	/* Infinite loop */
	for (;;) {
		if (HAL_GetTick() - tick > 10L) {
			cnt2 = __HAL_TIM_GET_COUNTER(&htim2);
			if (cnt2 > 32000) {
				dirL = 1;
				diff = (65536 - cnt2);
			} else {
				dirL = -1;
				diff = cnt2;
			}
			if (dirL == 1) {
				leftEncoderVal += diff;
			} else {
				leftEncoderVal -= diff;
			}
			__HAL_TIM_SET_COUNTER(&htim2, 0);

			tick = HAL_GetTick();
		}
	}

  /* USER CODE END StartEncoderLTask */
}

// ! Move car straight with the US as well
void moveCarStraightSensor(int usTarget)
{
	usTargetGLOBAL= usTarget;
	pwmVal_servo = SERVOCENTER;
	osDelay(100);
	straightUS = 1;
	control = 0;
	errorcorrection = 1;
	e_brake = 0;
	times_acceptable=0;
	while(finishCheck());


}

// ! Main task
void StartTask2(void *argument)
{
	//to be in straight 127 < x <189
	//IRdistance 2 is Right IR
	//change move car straight to allow for
  int pass = 0;
  for(;;)
  {
	if (pass) {
		break;
	}
    while(k!=1){
    	osDelay(50);
    }
    // aRxBuffer[0] = 'S';   //HERE IF HARDCODE -------------------------
    while(aRxBuffer[1] != 'S'){
    	osDelay(5);
    }
	//rightEncoderVal = leftEncoderVal=0;

	//errorcorrection = 1;
	times_acceptable=0;
//	osDelay(100);
//	while (firstDistance < 60) {
//		firstDistance = Distance;
//		osDelay(50);
//	}
	//IRCheck(SERVOCENTER);
	osDelay(100);

	// ! first movement
	moveCarStraightSensor(28); // doesnt change the direction


	// osDelay(100);
	// Pause to take picture
	HAL_UART_Transmit(&huart3, "A", 1,0xFFFF);
	// aRxBuffer[1]='L';
	nexttask = 'Z';
	while(nexttask == 'Z'){
		if(/*update==2 &&*/ aRxBuffer[2]=='L' || aRxBuffer[2]=='R'){
				nexttask = aRxBuffer[2];
		}
	}


    if(nexttask == 'L'){
    	moveCarLeft(50); // ! second movement
    	moveCarRight(55); // ! third movement, 105
    	finished();
    	if(aRxBuffer[0] == 'I'){

    	    	moveCarStraightSensor(35); //testing new shit
    	    	HAL_UART_Transmit(&huart3, "A", 1,0xFFFF);
    	    }
    	else
    	    		{
    				moveCarStraightSensor(35);
    	    		HAL_UART_Transmit(&huart3, "A", 1,0xFFFF);
    	    		}
//    	osDelay(50);
		//moveCarStraightSensor(28); //test
//		osDelay(50);

    }
    else if(nexttask == 'R'){
    	moveCarRight(50);
    	moveCarLeft(55);
    	finished();
//    	osDelay(50);
    	if(aRxBuffer[0] == 'I'){

    	moveCarStraightSensor(35); //testing new shit
    	HAL_UART_Transmit(&huart3, "A", 1,0xFFFF);
    }
    	else
    		{
    		moveCarStraightSensor(35);
    		HAL_UART_Transmit(&huart3, "A", 1,0xFFFF);
    		}
//    	osDelay(50);

    }

	// aRxBuffer[2] = 'R';
    nexttask = 'Z';
	while(nexttask == 'Z'){
		if(/*update==2 &&*/ aRxBuffer[3]=='L' || aRxBuffer[3]=='R'){
				nexttask = aRxBuffer[3];
		}
	}


	if(nexttask == 'L'){


		if (aRxBuffer[2] == 'L') {
//			moveCarLeft(95);
			moveCarLeft(65);
		} else if (aRxBuffer[2] == 'R'){
			moveCarLeft(85);
		} else {
			moveCarLeft(90);
		}
		osDelay(200);
		while(irDistance2<30){ // lets the car move until the IR detects less than 27
			control2 = 1;
			control3 = 1; // should not juke during the facing second obstacle

			IRCheck(SERVOCENTER); // sets control to 1, value inside is for servo motor
			// 150 is center, 105 is most left, 210 is most right
		}
		finished();
		osDelay(50);
		if (aRxBuffer[2] == 'L'){
			// 175 - 30 = 145
//			moveCarRightFaster(75);
//			moveCarRightFaster(70);
			moveCarRightFaster(145);
		} else if (aRxBuffer[2] == 'R') {
			// normal route
			moveCarRightFaster(175);
//			moveCarRightFaster(70);
//			moveCarRightFaster(105);
		}
//		moveCarRightFaster(175);

		while(irDistance2>30){ // lets the car move until the IR detects less than 27
			control2=1;
			IRCheck(SERVOCENTER); // sets control to 1, value inside is for servo motor
			// 150 is center, 105 is most left, 210 is most right
		}
		finished();
		osDelay(50);
		while(irDistance2<30){ // lets the car move until the IR detects less than 27
			control2=1;
			IRCheck(SERVOCENTER); // sets control to 1, value inside is for servo motor
			// 150 is center, 105 is most left, 210 is most right
		}
		finished();
		moveCarRight(90);
		moveCarRightFaster(58);
		moveCarLeftFaster(50); // 55
		finished();
		osDelay(30);
		while(irDistance2>30){ // lets the car move until the IR detects less than 27
			control2=1;
			control3=1;
			IRCheck(158); // sets control to 1, value inside is for servo motor
			// 150 is center, 105 is most left, 210 is most right
		}
		finished();
		if(irDistance2<20){
			IRCheck(SERVOCENTER);
			osDelay(100);
			moveCarRightFaster(45);
			moveCarLeftFaster(45);
			moveCarStraightSensor(20);

		}
		else
		if(irDistance2<30){
		IRCheck(SERVOCENTER);
		osDelay(100);
		moveCarRightFaster(60);
		moveCarLeftFaster(60);
		moveCarStraightSensor(20);
		}
		aRxBuffer[0]='E';
		aRxBuffer[1]='M';
		aRxBuffer[2]='P';
	}
	else if(nexttask == 'R'){

		if (aRxBuffer[2] == 'L') {
			moveCarRight(85);
		} else if (aRxBuffer[2] == 'R'){
//			moveCarRight(95); the slow route, doesn't need to turn full 95, it always overshot
			moveCarRight(65);
		} else {
			moveCarRight(90);
		}
		osDelay(200);
		while(irDistance1<30){ // lets the car move until the IR detects less than 27
			control2 = 1;
			control3 = 1;
			IRCheck(SERVOCENTER); // sets control to 1, value inside is for servo motor
		}
		finished();
		if (aRxBuffer[2] == 'R') {
			// smart turns originally 175, but minus 30
//			moveCarLeftFaster(75);
//			moveCarLeftFaster(70);
			moveCarLeftFaster(145);
		} else if (aRxBuffer[2] == 'L') {
			// normal route turns
			moveCarLeftFaster(175);
//			moveCarLeftFaster(70);
//			moveCarLeftFaster(105);
		}
		while(irDistance1>30){ // lets the car move until the IR detects less than 27
			control2=1;
			IRCheck(SERVOCENTER); // sets control to 1, value inside is for servo motor
		}
		finished();
		osDelay(50);
		while(irDistance1<30){ // lets the car move until the IR detects less than 27
			control2=1;
			IRCheck(SERVOCENTER); // sets control to 1, value inside is for servo motor
			// 150 is center, 105 is most left, 210 is most right
		}
		finished();
		moveCarLeft(90);
		moveCarLeftFaster(57);
		moveCarRightFaster(50); // 55
		finished();
		osDelay(30);
		while(irDistance1>30){ // lets the car move until the IR detects less than 27
			control2=1; // moving slowly for checking ir
			control3=1;
			IRCheck(146); // sets control to 1, value inside is for servo motor
			// 150 is center, 105 is most left, 210 is most right
		}
		finished();
		if(irDistance1<20){
			IRCheck(SERVOCENTER);
			osDelay(100);
			moveCarLeftFaster(45);
			moveCarRightFaster(45);
			moveCarStraightSensor(20);
		}
		else
		if(irDistance1<30){
		IRCheck(SERVOCENTER);
		osDelay(100);
		moveCarLeftFaster(60);
		moveCarRightFaster(60);
		moveCarStraightSensor(20);
		}
		aRxBuffer[0]='E';
		aRxBuffer[1]='M';
		aRxBuffer[2]='P';
	}
	pass = 1;
  }
  /* USER CODE END StartTask2 */
}

// ! Start IR task, to read
void StartIRTask(void *argument)
{
  /* USER CODE BEGIN StartIRTask */
  /* Infinite loop */
  uint32_t tick = 0;
  for(;;)
  {
	if (HAL_GetTick() - tick >= 2) {
	    HAL_ADC_Start(&hadc1);
		HAL_ADC_PollForConversion(&hadc1, 10);
		ADC_VAL1 = HAL_ADC_GetValue(&hadc1);
		HAL_ADC_Stop(&hadc1);

		HAL_ADC_Start(&hadc2);
		HAL_ADC_PollForConversion(&hadc2, 10);
		ADC_VAL2 = HAL_ADC_GetValue(&hadc2);
		HAL_ADC_Stop(&hadc2);
		voltage1 = (float) (ADC_VAL1*5)/4095;
		irDistance1 = roundf(29.988 *pow(voltage1 , -1.173));
		voltage2 = (float) (ADC_VAL2*5)/4095;
		irDistance2 = roundf(29.988 *pow(voltage2 , -1.173));
		tick = HAL_GetTick();
	}
  }
  /* USER CODE END StartIRTask */
}

void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
	/* User can add his own implementation to report the HAL error return state */
	__disable_irq();
	while (1) {
	}
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
