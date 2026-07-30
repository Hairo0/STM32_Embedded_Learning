/*
 * bmp280.c
 *
 *  Created on: 29 Tem 2026
 *      Author: sbozk
 */

#include "bmp280.h"
#include "config.h"

static int32_t t_fine;

error_t BMP280_Init(I2C_HandleTypeDef *hi2c) {

	uint8_t config_data = 0xB7;

	    if (HAL_I2C_Mem_Write(hi2c, BMP280_ADDRESS, 0xF4, I2C_MEMADD_SIZE_8BIT, &config_data, 1, 100) != HAL_OK) {
	        return ERROR_SENSOR_NOT_FOUND;
	    }

	    return ERROR_OK;
	}

error_t BMP280_ReadTrimmingParameters(I2C_HandleTypeDef *hi2c, BMP280_Trimming_Parameters *parameters) {

	uint8_t bmp280_temp[24];

	HAL_I2C_Mem_Read(hi2c, BMP280_ADDRESS, 0X88, I2C_MEMADD_SIZE_8BIT, bmp280_temp, 24, 100);

	parameters->dig_T1 = (uint16_t) ((bmp280_temp[1] << 8) | bmp280_temp[0]);
	parameters->dig_T2 = (int16_t) ((bmp280_temp[3] << 8) | bmp280_temp[2]);
	parameters->dig_T3 = (int16_t) ((bmp280_temp[5] << 8) | bmp280_temp[4]);
	parameters->dig_P1 = (uint16_t) ((bmp280_temp[7] << 8) | bmp280_temp[6]);
	parameters->dig_P2 = (int16_t) ((bmp280_temp[9] << 8) | bmp280_temp[8]);
	parameters->dig_P3 = (int16_t) ((bmp280_temp[11] << 8) | bmp280_temp[10]);
	parameters->dig_P4 = (int16_t) ((bmp280_temp[13] << 8) | bmp280_temp[12]);
	parameters->dig_P5 = (int16_t) ((bmp280_temp[15] << 8) | bmp280_temp[14]);
	parameters->dig_P6 = (int16_t) ((bmp280_temp[17] << 8) | bmp280_temp[16]);
	parameters->dig_P7 = (int16_t) ((bmp280_temp[19] << 8) | bmp280_temp[18]);
	parameters->dig_P8 = (int16_t) ((bmp280_temp[21] << 8) | bmp280_temp[20]);
	parameters->dig_P9 = (int16_t) ((bmp280_temp[23] << 8) | bmp280_temp[22]);

	return ERROR_OK;
}

error_t BMP280_ReadRawTemperature(I2C_HandleTypeDef *hi2c, int32_t *raw_temperature) {

	uint8_t raw_data[3];

	HAL_I2C_Mem_Read(hi2c, BMP280_ADDRESS, 0XFA, I2C_MEMADD_SIZE_8BIT, raw_data, 3, 100);

	*raw_temperature =
			(((uint32_t) raw_data[0] << 12) | ((uint32_t) (raw_data[1] << 4)) | ((uint32_t) (raw_data[2] >> 4)));

	return ERROR_OK;
}

error_t BMP280_ReadRawPressure(I2C_HandleTypeDef *hi2c, int32_t *raw_pressure) {

	uint8_t raw_data[3];

	HAL_I2C_Mem_Read(hi2c, BMP280_ADDRESS, 0XF7, I2C_MEMADD_SIZE_8BIT, raw_data, 3, 100);

	*raw_pressure =
			(((uint32_t) raw_data[0] << 12) | ((uint32_t) (raw_data[1] << 4)) | ((uint32_t) (raw_data[2] >> 4)));

	return ERROR_OK;
}


float BMP280_CalculateTemperature (int32_t raw_temperature, const BMP280_Trimming_Parameters *parameters){

		// Returns temperature in DegC, resolution is 0.01 DegC. Output value of “5123” equals 51.23 DegC.

		// t_fine carries fine temperature as global value


		int32_t var1, var2, T;

		var1 = ((((raw_temperature>>3) - ((int32_t)parameters->dig_T1<<1))) * ((int32_t)parameters->dig_T2)) >> 11;

		var2 = (((((raw_temperature>>4) - ((int32_t)parameters->dig_T1)) * ((raw_temperature>>4) - ((int32_t)parameters->dig_T1)))

		>> 12) *

		((int32_t)parameters->dig_T3)) >> 14;

		t_fine = var1 + var2;

		T = (t_fine * 5 + 128) >> 8;

		return (float)T/100;


}


float BMP280_CalculatePressure (int32_t raw_pressure, const BMP280_Trimming_Parameters *parameters){

	// Returns pressure in Pa as unsigned 32 bit integer in Q24.8 format (24 integer bits and 8	fractional bits).
	// Output value of “24674867” represents 24674867/256 = 96386.2 Pa = 963.862 hPa

	int64_t var1, var2, p;

	var1 = ((int64_t) t_fine) - 128000;
	var2 = var1 * var1 * (int64_t)parameters->dig_P6;
	var2 = var2 + ((var1*(int64_t)parameters->dig_P5)<<17);
	var2 = var2 + (((int64_t)parameters->dig_P4)<<35);
	var1 = ((var1 * var1 * (int64_t)parameters->dig_P3)>>8) + ((var1 * (int64_t)parameters->dig_P2)<<12);
	var1 = (((((int64_t)1)<<47)+var1))*((int64_t)parameters->dig_P1)>>33;
	if (var1 == 0)
	{
	return 0; // avoid exception caused by division by zero
	}
	p = 1048576-raw_pressure;
	p = (((p<<31)-var2)*3125)/var1;
	var1 = (((int64_t)parameters->dig_P9) * (p>>13) * (p>>13)) >> 25;
	var2 = (((int64_t)parameters->dig_P8) * p) >> 19;
	p = ((p + var1 + var2) >> 8) + (((int64_t)parameters->dig_P7)<<4);
	return (float)p / 256 / 100;
}
