/*
 * mpu6050.h
 *
 *  Created on: 31 Tem 2026
 *      Author: sbozk
 */

#ifndef INC_MPU6050_H_
#define INC_MPU6050_H_

#include "main.h"
#include "config.h"

typedef struct {

	int16_t ACCEL_X;
	int16_t ACCEL_Y;
	int16_t ACCEL_Z;
	int16_t GYRO_X;
	int16_t GYRO_Y;
	int16_t GYRO_Z;
} MPU6050_ACCEL_GYRO;

error_t MPU6050_Init(I2C_HandleTypeDef *hi2c);

error_t MPU6050_ReadRawAccelGyro(I2C_HandleTypeDef *hi2c, MPU6050_ACCEL_GYRO *raw_accel_gyro);

#endif /* INC_MPU6050_H_ */
