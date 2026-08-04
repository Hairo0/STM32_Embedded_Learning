	/*
	 * mpu6050.c
	 *
	 *  Created on: 31 Tem 2026
	 *      Author: sbozk
	 */

	#include "config.h"
	#include "mpu6050.h"

	error_t MPU6050_Init(I2C_HandleTypeDef *hi2c){

		uint8_t config_data=0x00;
		uint8_t interrupt_data=0x01;

			if (HAL_I2C_Mem_Write(hi2c, MPU6050_ADDRESS, MPU6050_PWR_MGMT_1, I2C_MEMADD_SIZE_8BIT, &config_data, 1, 100) != HAL_OK){
							return ERROR_SENSOR_NOT_FOUND;
						}


			if (HAL_I2C_Mem_Write(hi2c, MPU6050_ADDRESS, MPU6050_INTERRUPT_ENABLE, I2C_MEMADD_SIZE_8BIT, &interrupt_data , 1, 100) != HAL_OK){

							return ERROR_SENSOR_NOT_FOUND;
						}

						return ERROR_OK;
	}

	error_t MPU6050_ReadRealAccelGyro(I2C_HandleTypeDef *hi2c, MPU6050_ACCEL_GYRO *real_accel_gyro){

		uint8_t raw_data[14];

		if (HAL_I2C_Mem_Read(hi2c, MPU6050_ADDRESS, 0x3B, I2C_MEMADD_SIZE_8BIT, raw_data, 14, 100) != HAL_OK) {
		        return ERROR_SENSOR_NOT_FOUND;
		    }

		real_accel_gyro->ACCEL_X = (int16_t) ((raw_data[0]<<8) | raw_data[1]) / 16384.0f;
		real_accel_gyro->ACCEL_Y = (int16_t) ((raw_data[2]<<8) | raw_data[3]) / 16384.0f;
		real_accel_gyro->ACCEL_Z = (int16_t) ((raw_data[4]<<8) | raw_data[5]) / 16384.0f;
		real_accel_gyro->GYRO_X = (int16_t) ((raw_data[8]<<8) | raw_data[9]) / 131.0f;
		real_accel_gyro->GYRO_Y = (int16_t) ((raw_data[10]<<8) | raw_data[11]) / 131.0f;
		real_accel_gyro->GYRO_Z = (int16_t) ((raw_data[12]<<8) | raw_data[13]) / 131.0f;


		return ERROR_OK;
	}
