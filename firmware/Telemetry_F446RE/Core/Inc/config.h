/*
 * config.h
 *
 *  Created on: 28 Tem 2026
 *      Author: sbozk
 */

#ifndef INC_CONFIG_H_
#define INC_CONFIG_H_

#include <stdint.h>
#include <stdbool.h>

#define HEADER_1 0XAA
#define HEADER_2 0X55

#define BMP280_ADDRESS (0X76 << 1)
#define MPU6050_ADDRESS (0X68 << 1)

#define BMP280_ID_ADDRESS 0xD0
#define BMP280_ID_RESET 0X58

#define MPU6050_WHO_AM_I_REG 0x75
#define MPU6050_WHO_AM_I_VAL 0x70
#define MPU6050_PWR_MGMT_1 0x6B
#define MPU6050_INTERRUPT_ENABLE 0X38


typedef enum {


	ERROR_OK = 0,
	ERROR_TIMEOUT = 1,
	ERROR_SENSOR_NOT_FOUND = 2,

} error_t;


#endif /* INC_CONFIG_H_ */
