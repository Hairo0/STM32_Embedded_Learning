/*
 * bmp280.h
 *
 *  Created on: 29 Tem 2026
 *      Author: sbozk
 */

#ifndef INC_BMP280_H_
#define INC_BMP280_H_

#include "main.h"
#include "config.h"

typedef struct {

	uint16_t dig_T1;
	int16_t  dig_T2;
	int16_t  dig_T3;
	uint16_t dig_P1;
	int16_t  dig_P2;
	int16_t  dig_P3;
	int16_t  dig_P4;
	int16_t  dig_P5;
	int16_t  dig_P6;
	int16_t  dig_P7;
	int16_t  dig_P8;
	int16_t  dig_P9;

}BMP280_Trimming_Parameters;

error_t BMP280_Init(I2C_HandleTypeDef *hi2c);

error_t BMP280_ReadTrimmingParameters(I2C_HandleTypeDef *hi2c, BMP280_Trimming_Parameters *parameters);

error_t BMP280_ReadRawTemperature(I2C_HandleTypeDef *hi2c, int32_t *raw_temperature);

error_t BMP280_ReadRawPressure(I2C_HandleTypeDef *hi2c, int32_t *raw_pressure);

float BMP280_CalculateTemperature (int32_t raw_temperature, const BMP280_Trimming_Parameters *parameters);

float BMP280_CalculatePressure(int32_t raw_pressure, const BMP280_Trimming_Parameters *parameters);


#endif /* INC_BMP280_H_ */
