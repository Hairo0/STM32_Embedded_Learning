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
#define MPU6050_ADDRESS (0X69 << 1)

#define BMP280_ID_ADDRESS 0xD0
#define BMP280_ID_RESET 0X58


#define MPU6050_PWR_MGMT_1 0x6B
#define MPU6050_INTERRUPT_ENABLE 0X38


typedef enum {


	ERROR_OK = 0,
	ERROR_TIMEOUT = 1,
	ERROR_SENSOR_NOT_FOUND = 2,

} error_t;

#pragma pack(push, 1)

typedef struct {

	uint8_t header1;
	uint8_t header2;

	uint16_t sequence_number;
	uint8_t payload_length;
	uint8_t packet_type;

	float accel_x;
	float accel_y;
	float accel_z;
	float gyro_x;
	float gyro_y;
	float gyro_z;
	float temperature;
	float pressure;

	uint16_t crc;

} TelemetryPacket_t;

#pragma pack(pop)

static inline uint16_t crc_function(uint8_t *buffer, uint16_t length) {
    uint16_t crc = 0x0000;
    for (uint16_t i = 0; i < length; i++) {
        crc ^= (uint16_t)buffer[i] << 8;
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ 0x1021;
            } else {
                crc = crc << 1;
            }
        }
    }
    return crc;
}

#endif /* INC_CONFIG_H_ */
