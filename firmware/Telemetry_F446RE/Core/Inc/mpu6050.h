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

	float ACCEL_X;
	float ACCEL_Y;
	float ACCEL_Z;
	float GYRO_X;
	float GYRO_Y;
	float GYRO_Z;
} MPU6050_ACCEL_GYRO;

error_t MPU6050_Init(I2C_HandleTypeDef *hi2c);

error_t MPU6050_ReadRealAccelGyro(I2C_HandleTypeDef *hi2c, MPU6050_ACCEL_GYRO *real_accel_gyro);

#endif /* INC_MPU6050_H_ */
