#ifndef UART_H
#define UART_H

#include <stdint.h>
#include "fixed_point.h"

void uart_init(void);
void uart_putc(char c);
void uart_puts(const char *s);
void uart_puts_P(const char *s);
void uart_put_fixed(fixed_t val);
void uart_put_u16(uint16_t val);

#endif
