#include "uart.h"
#include <avr/io.h>
#include <avr/pgmspace.h>
#include <stdlib.h>

void uart_init(void)
{
    PORTD.OUTSET = PIN3_bm;
    PORTD.DIRSET = PIN3_bm;
    PORTD.DIRCLR = PIN2_bm;

    /* 115200 baud @ 32 MHz, CLK2X: BSEL=34, BSCALE=0 -> 0.8% error */
    USARTD0.BAUDCTRLA = 34;
    USARTD0.BAUDCTRLB = 0;
    USARTD0.CTRLB     = USART_CLK2X_bm | USART_TXEN_bm;
    USARTD0.CTRLC     = USART_CHSIZE_8BIT_gc;
}

void uart_putc(char c)
{
    while (!(USARTD0.STATUS & USART_DREIF_bm))
        ;
    USARTD0.DATA = c;
}

void uart_puts(const char *s)
{
    while (*s)
        uart_putc(*s++);
}

void uart_puts_P(const char *s)
{
    char c;
    while ((c = pgm_read_byte(s++)))
        uart_putc(c);
}

void uart_put_fixed(fixed_t val)
{
    char buf[12];
    ltoa((long)val, buf, 10);
    uart_puts(buf);
}

void uart_put_u16(uint16_t val)
{
    char buf[6];
    utoa(val, buf, 10);
    uart_puts(buf);
}
