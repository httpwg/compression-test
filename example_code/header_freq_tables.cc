#include <utility>
#include <array>

#include "header_freq_tables.h"

FreqTable FreqTables::request_freq_table = {
{
  std::pair<uint16_t, uint32_t>(0x00U,    0),
  std::pair<uint16_t, uint32_t>(0x01U,    0),
  std::pair<uint16_t, uint32_t>(0x02U,    0),
  std::pair<uint16_t, uint32_t>(0x03U,    0),
  std::pair<uint16_t, uint32_t>(0x04U,    0),
  std::pair<uint16_t, uint32_t>(0x05U,    0),
  std::pair<uint16_t, uint32_t>(0x06U,    0),
  std::pair<uint16_t, uint32_t>(0x07U,    0),
  std::pair<uint16_t, uint32_t>(0x08U,    0),
  std::pair<uint16_t, uint32_t>('\t' ,    0),
  std::pair<uint16_t, uint32_t>('\n' ,    0),
  std::pair<uint16_t, uint32_t>(0x0bU,    0),
  std::pair<uint16_t, uint32_t>(0x0cU,    0),
  std::pair<uint16_t, uint32_t>('\r' ,    0),
  std::pair<uint16_t, uint32_t>(0x0eU,    0),
  std::pair<uint16_t, uint32_t>(0x0fU,    0),
  std::pair<uint16_t, uint32_t>(0x10U,    0),
  std::pair<uint16_t, uint32_t>(0x11U,    0),
  std::pair<uint16_t, uint32_t>(0x12U,    0),
  std::pair<uint16_t, uint32_t>(0x13U,    0),
  std::pair<uint16_t, uint32_t>(0x14U,    0),
  std::pair<uint16_t, uint32_t>(0x15U,    0),
  std::pair<uint16_t, uint32_t>(0x16U,    0),
  std::pair<uint16_t, uint32_t>(0x17U,    0),
  std::pair<uint16_t, uint32_t>(0x18U,    0),
  std::pair<uint16_t, uint32_t>(0x19U,    0),
  std::pair<uint16_t, uint32_t>(0x1aU,    0),
  std::pair<uint16_t, uint32_t>(0x1bU,    0),
  std::pair<uint16_t, uint32_t>(0x1cU,    0),
  std::pair<uint16_t, uint32_t>(0x1dU,    0),
  std::pair<uint16_t, uint32_t>(0x1eU,    0),
  std::pair<uint16_t, uint32_t>(0x1fU,    0),
  std::pair<uint16_t, uint32_t>(' '  ,   28),
  std::pair<uint16_t, uint32_t>('!'  ,   39),
  std::pair<uint16_t, uint32_t>('"'  ,    0),
  std::pair<uint16_t, uint32_t>('#'  ,    0),
  std::pair<uint16_t, uint32_t>('$'  ,    2),
  std::pair<uint16_t, uint32_t>('%'  , 1055),
  std::pair<uint16_t, uint32_t>('&'  , 1580),
  std::pair<uint16_t, uint32_t>('\'' ,    2),
  std::pair<uint16_t, uint32_t>('('  ,   20),
  std::pair<uint16_t, uint32_t>(')'  ,   20),
  std::pair<uint16_t, uint32_t>('*'  ,   17),
  std::pair<uint16_t, uint32_t>('+'  ,    2),
  std::pair<uint16_t, uint32_t>(','  ,  883),
  std::pair<uint16_t, uint32_t>('-'  , 1150),
  std::pair<uint16_t, uint32_t>('.'  , 2225),
  std::pair<uint16_t, uint32_t>('/'  , 3671),
  std::pair<uint16_t, uint32_t>('0'  , 2630),
  std::pair<uint16_t, uint32_t>('1'  , 2997),
  std::pair<uint16_t, uint32_t>('2'  , 3089),
  std::pair<uint16_t, uint32_t>('3'  , 2437),
  std::pair<uint16_t, uint32_t>('4'  , 2009),
  std::pair<uint16_t, uint32_t>('5'  , 1637),
  std::pair<uint16_t, uint32_t>('6'  , 2011),
  std::pair<uint16_t, uint32_t>('7'  , 1508),
  std::pair<uint16_t, uint32_t>('8'  , 1689),
  std::pair<uint16_t, uint32_t>('9'  , 1524),
  std::pair<uint16_t, uint32_t>(':'  ,  146),
  std::pair<uint16_t, uint32_t>(';'  ,  122),
  std::pair<uint16_t, uint32_t>('<'  ,    0),
  std::pair<uint16_t, uint32_t>('='  , 2014),
  std::pair<uint16_t, uint32_t>('>'  ,    0),
  std::pair<uint16_t, uint32_t>('?'  ,  261),
  std::pair<uint16_t, uint32_t>('@'  ,    0),
  std::pair<uint16_t, uint32_t>('A'  ,  788),
  std::pair<uint16_t, uint32_t>('B'  ,  404),
  std::pair<uint16_t, uint32_t>('C'  ,  548),
  std::pair<uint16_t, uint32_t>('D'  ,  602),
  std::pair<uint16_t, uint32_t>('E'  ,  386),
  std::pair<uint16_t, uint32_t>('F'  ,  470),
  std::pair<uint16_t, uint32_t>('G'  ,  427),
  std::pair<uint16_t, uint32_t>('H'  ,  391),
  std::pair<uint16_t, uint32_t>('I'  ,  498),
  std::pair<uint16_t, uint32_t>('J'  ,  157),
  std::pair<uint16_t, uint32_t>('K'  ,  205),
  std::pair<uint16_t, uint32_t>('L'  ,  371),
  std::pair<uint16_t, uint32_t>('M'  ,  242),
  std::pair<uint16_t, uint32_t>('N'  ,  366),
  std::pair<uint16_t, uint32_t>('O'  ,  316),
  std::pair<uint16_t, uint32_t>('P'  ,  292),
  std::pair<uint16_t, uint32_t>('Q'  ,  253),
  std::pair<uint16_t, uint32_t>('R'  ,  293),
  std::pair<uint16_t, uint32_t>('S'  ,  380),
  std::pair<uint16_t, uint32_t>('T'  ,  312),
  std::pair<uint16_t, uint32_t>('U'  ,  333),
  std::pair<uint16_t, uint32_t>('V'  ,  359),
  std::pair<uint16_t, uint32_t>('W'  ,  195),
  std::pair<uint16_t, uint32_t>('X'  ,  257),
  std::pair<uint16_t, uint32_t>('Y'  ,  244),
  std::pair<uint16_t, uint32_t>('Z'  ,  227),
  std::pair<uint16_t, uint32_t>('['  ,    2),
  std::pair<uint16_t, uint32_t>('\\' ,    0),
  std::pair<uint16_t, uint32_t>(']'  ,    2),
  std::pair<uint16_t, uint32_t>('^'  ,    0),
  std::pair<uint16_t, uint32_t>('_'  , 1413),
  std::pair<uint16_t, uint32_t>('`'  ,    0),
  std::pair<uint16_t, uint32_t>('a'  , 3449),
  std::pair<uint16_t, uint32_t>('b'  , 1231),
  std::pair<uint16_t, uint32_t>('c'  , 2375),
  std::pair<uint16_t, uint32_t>('d'  , 1586),
  std::pair<uint16_t, uint32_t>('e'  , 3543),
  std::pair<uint16_t, uint32_t>('f'  ,  843),
  std::pair<uint16_t, uint32_t>('g'  , 1853),
  std::pair<uint16_t, uint32_t>('h'  , 1003),
  std::pair<uint16_t, uint32_t>('i'  , 2713),
  std::pair<uint16_t, uint32_t>('j'  ,  781),
  std::pair<uint16_t, uint32_t>('k'  ,  533),
  std::pair<uint16_t, uint32_t>('l'  , 1660),
  std::pair<uint16_t, uint32_t>('m'  , 2005),
  std::pair<uint16_t, uint32_t>('n'  , 2559),
  std::pair<uint16_t, uint32_t>('o'  , 2296),
  std::pair<uint16_t, uint32_t>('p'  , 1963),
  std::pair<uint16_t, uint32_t>('q'  ,  394),
  std::pair<uint16_t, uint32_t>('r'  , 1931),
  std::pair<uint16_t, uint32_t>('s'  , 3180),
  std::pair<uint16_t, uint32_t>('t'  , 2747),
  std::pair<uint16_t, uint32_t>('u'  ,  972),
  std::pair<uint16_t, uint32_t>('v'  ,  791),
  std::pair<uint16_t, uint32_t>('w'  ,  776),
  std::pair<uint16_t, uint32_t>('x'  ,  562),
  std::pair<uint16_t, uint32_t>('y'  ,  704),
  std::pair<uint16_t, uint32_t>('z'  ,  351),
  std::pair<uint16_t, uint32_t>('{'  ,   11),
  std::pair<uint16_t, uint32_t>('|'  ,    0),
  std::pair<uint16_t, uint32_t>('}'  ,   11),
  std::pair<uint16_t, uint32_t>('~'  ,    2),
  std::pair<uint16_t, uint32_t>(0x7fU,    0),
  std::pair<uint16_t, uint32_t>(0x80U,    0),
  std::pair<uint16_t, uint32_t>(0x81U,    0),
  std::pair<uint16_t, uint32_t>(0x82U,    0),
  std::pair<uint16_t, uint32_t>(0x83U,    0),
  std::pair<uint16_t, uint32_t>(0x84U,    0),
  std::pair<uint16_t, uint32_t>(0x85U,    0),
  std::pair<uint16_t, uint32_t>(0x86U,    0),
  std::pair<uint16_t, uint32_t>(0x87U,    0),
  std::pair<uint16_t, uint32_t>(0x88U,    0),
  std::pair<uint16_t, uint32_t>(0x89U,    0),
  std::pair<uint16_t, uint32_t>(0x8aU,    0),
  std::pair<uint16_t, uint32_t>(0x8bU,    0),
  std::pair<uint16_t, uint32_t>(0x8cU,    0),
  std::pair<uint16_t, uint32_t>(0x8dU,    0),
  std::pair<uint16_t, uint32_t>(0x8eU,    0),
  std::pair<uint16_t, uint32_t>(0x8fU,    0),
  std::pair<uint16_t, uint32_t>(0x90U,    0),
  std::pair<uint16_t, uint32_t>(0x91U,    0),
  std::pair<uint16_t, uint32_t>(0x92U,    0),
  std::pair<uint16_t, uint32_t>(0x93U,    0),
  std::pair<uint16_t, uint32_t>(0x94U,    0),
  std::pair<uint16_t, uint32_t>(0x95U,    0),
  std::pair<uint16_t, uint32_t>(0x96U,    0),
  std::pair<uint16_t, uint32_t>(0x97U,    0),
  std::pair<uint16_t, uint32_t>(0x98U,    0),
  std::pair<uint16_t, uint32_t>(0x99U,    0),
  std::pair<uint16_t, uint32_t>(0x9aU,    0),
  std::pair<uint16_t, uint32_t>(0x9bU,    0),
  std::pair<uint16_t, uint32_t>(0x9cU,    0),
  std::pair<uint16_t, uint32_t>(0x9dU,    0),
  std::pair<uint16_t, uint32_t>(0x9eU,    0),
  std::pair<uint16_t, uint32_t>(0x9fU,    0),
  std::pair<uint16_t, uint32_t>(0xa0U,    0),
  std::pair<uint16_t, uint32_t>(0xa1U,    0),
  std::pair<uint16_t, uint32_t>(0xa2U,    0),
  std::pair<uint16_t, uint32_t>(0xa3U,    0),
  std::pair<uint16_t, uint32_t>(0xa4U,    0),
  std::pair<uint16_t, uint32_t>(0xa5U,    0),
  std::pair<uint16_t, uint32_t>(0xa6U,    0),
  std::pair<uint16_t, uint32_t>(0xa7U,    0),
  std::pair<uint16_t, uint32_t>(0xa8U,    0),
  std::pair<uint16_t, uint32_t>(0xa9U,    0),
  std::pair<uint16_t, uint32_t>(0xaaU,    0),
  std::pair<uint16_t, uint32_t>(0xabU,    0),
  std::pair<uint16_t, uint32_t>(0xacU,    0),
  std::pair<uint16_t, uint32_t>(0xadU,    0),
  std::pair<uint16_t, uint32_t>(0xaeU,    0),
  std::pair<uint16_t, uint32_t>(0xafU,    0),
  std::pair<uint16_t, uint32_t>(0xb0U,    0),
  std::pair<uint16_t, uint32_t>(0xb1U,    0),
  std::pair<uint16_t, uint32_t>(0xb2U,    0),
  std::pair<uint16_t, uint32_t>(0xb3U,    0),
  std::pair<uint16_t, uint32_t>(0xb4U,    0),
  std::pair<uint16_t, uint32_t>(0xb5U,    0),
  std::pair<uint16_t, uint32_t>(0xb6U,    0),
  std::pair<uint16_t, uint32_t>(0xb7U,    0),
  std::pair<uint16_t, uint32_t>(0xb8U,    0),
  std::pair<uint16_t, uint32_t>(0xb9U,    0),
  std::pair<uint16_t, uint32_t>(0xbaU,    0),
  std::pair<uint16_t, uint32_t>(0xbbU,    0),
  std::pair<uint16_t, uint32_t>(0xbcU,    0),
  std::pair<uint16_t, uint32_t>(0xbdU,    0),
  std::pair<uint16_t, uint32_t>(0xbeU,    0),
  std::pair<uint16_t, uint32_t>(0xbfU,    0),
  std::pair<uint16_t, uint32_t>(0xc0U,    0),
  std::pair<uint16_t, uint32_t>(0xc1U,    0),
  std::pair<uint16_t, uint32_t>(0xc2U,    0),
  std::pair<uint16_t, uint32_t>(0xc3U,    0),
  std::pair<uint16_t, uint32_t>(0xc4U,    0),
  std::pair<uint16_t, uint32_t>(0xc5U,    0),
  std::pair<uint16_t, uint32_t>(0xc6U,    0),
  std::pair<uint16_t, uint32_t>(0xc7U,    0),
  std::pair<uint16_t, uint32_t>(0xc8U,    0),
  std::pair<uint16_t, uint32_t>(0xc9U,    0),
  std::pair<uint16_t, uint32_t>(0xcaU,    0),
  std::pair<uint16_t, uint32_t>(0xcbU,    0),
  std::pair<uint16_t, uint32_t>(0xccU,    0),
  std::pair<uint16_t, uint32_t>(0xcdU,    0),
  std::pair<uint16_t, uint32_t>(0xceU,    0),
  std::pair<uint16_t, uint32_t>(0xcfU,    0),
  std::pair<uint16_t, uint32_t>(0xd0U,    0),
  std::pair<uint16_t, uint32_t>(0xd1U,    0),
  std::pair<uint16_t, uint32_t>(0xd2U,    0),
  std::pair<uint16_t, uint32_t>(0xd3U,    0),
  std::pair<uint16_t, uint32_t>(0xd4U,    0),
  std::pair<uint16_t, uint32_t>(0xd5U,    0),
  std::pair<uint16_t, uint32_t>(0xd6U,    0),
  std::pair<uint16_t, uint32_t>(0xd7U,    0),
  std::pair<uint16_t, uint32_t>(0xd8U,    0),
  std::pair<uint16_t, uint32_t>(0xd9U,    0),
  std::pair<uint16_t, uint32_t>(0xdaU,    0),
  std::pair<uint16_t, uint32_t>(0xdbU,    0),
  std::pair<uint16_t, uint32_t>(0xdcU,    0),
  std::pair<uint16_t, uint32_t>(0xddU,    0),
  std::pair<uint16_t, uint32_t>(0xdeU,    0),
  std::pair<uint16_t, uint32_t>(0xdfU,    0),
  std::pair<uint16_t, uint32_t>(0xe0U,    0),
  std::pair<uint16_t, uint32_t>(0xe1U,    0),
  std::pair<uint16_t, uint32_t>(0xe2U,    0),
  std::pair<uint16_t, uint32_t>(0xe3U,    0),
  std::pair<uint16_t, uint32_t>(0xe4U,    0),
  std::pair<uint16_t, uint32_t>(0xe5U,    0),
  std::pair<uint16_t, uint32_t>(0xe6U,    0),
  std::pair<uint16_t, uint32_t>(0xe7U,    0),
  std::pair<uint16_t, uint32_t>(0xe8U,    0),
  std::pair<uint16_t, uint32_t>(0xe9U,    0),
  std::pair<uint16_t, uint32_t>(0xeaU,    0),
  std::pair<uint16_t, uint32_t>(0xebU,    0),
  std::pair<uint16_t, uint32_t>(0xecU,    0),
  std::pair<uint16_t, uint32_t>(0xedU,    0),
  std::pair<uint16_t, uint32_t>(0xeeU,    0),
  std::pair<uint16_t, uint32_t>(0xefU,    0),
  std::pair<uint16_t, uint32_t>(0xf0U,    0),
  std::pair<uint16_t, uint32_t>(0xf1U,    0),
  std::pair<uint16_t, uint32_t>(0xf2U,    0),
  std::pair<uint16_t, uint32_t>(0xf3U,    0),
  std::pair<uint16_t, uint32_t>(0xf4U,    0),
  std::pair<uint16_t, uint32_t>(0xf5U,    0),
  std::pair<uint16_t, uint32_t>(0xf6U,    0),
  std::pair<uint16_t, uint32_t>(0xf7U,    0),
  std::pair<uint16_t, uint32_t>(0xf8U,    0),
  std::pair<uint16_t, uint32_t>(0xf9U,    0),
  std::pair<uint16_t, uint32_t>(0xfaU,    0),
  std::pair<uint16_t, uint32_t>(0xfbU,    0),
  std::pair<uint16_t, uint32_t>(0xfcU,    0),
  std::pair<uint16_t, uint32_t>(0xfdU,    0),
  std::pair<uint16_t, uint32_t>(0xfeU,    0),
  std::pair<uint16_t, uint32_t>(0xffU,    0),
  std::pair<uint16_t, uint32_t>(  256, 1093),
}
};

FreqTable FreqTables::response_freq_table = {
{
  std::pair<uint16_t, uint32_t>(0x00,   57),
  std::pair<uint16_t, uint32_t>(0x01,    0),
  std::pair<uint16_t, uint32_t>(0x02,    0),
  std::pair<uint16_t, uint32_t>(0x03,    0),
  std::pair<uint16_t, uint32_t>(0x04,    0),
  std::pair<uint16_t, uint32_t>(0x05,    0),
  std::pair<uint16_t, uint32_t>(0x06,    0),
  std::pair<uint16_t, uint32_t>(0x07,    0),
  std::pair<uint16_t, uint32_t>(0x08,    0),
  std::pair<uint16_t, uint32_t>('\t',    0),
  std::pair<uint16_t, uint32_t>('\n',    0),
  std::pair<uint16_t, uint32_t>(0x0b,    0),
  std::pair<uint16_t, uint32_t>(0x0c,    0),
  std::pair<uint16_t, uint32_t>('\r',    0),
  std::pair<uint16_t, uint32_t>(0x0e,    0),
  std::pair<uint16_t, uint32_t>(0x0f,    0),
  std::pair<uint16_t, uint32_t>(0x10,    0),
  std::pair<uint16_t, uint32_t>(0x11,    0),
  std::pair<uint16_t, uint32_t>(0x12,    0),
  std::pair<uint16_t, uint32_t>(0x13,    0),
  std::pair<uint16_t, uint32_t>(0x14,    0),
  std::pair<uint16_t, uint32_t>(0x15,    0),
  std::pair<uint16_t, uint32_t>(0x16,    0),
  std::pair<uint16_t, uint32_t>(0x17,    0),
  std::pair<uint16_t, uint32_t>(0x18,    0),
  std::pair<uint16_t, uint32_t>(0x19,    0),
  std::pair<uint16_t, uint32_t>(0x1a,    0),
  std::pair<uint16_t, uint32_t>(0x1b,    0),
  std::pair<uint16_t, uint32_t>(0x1c,    0),
  std::pair<uint16_t, uint32_t>(0x1d,    0),
  std::pair<uint16_t, uint32_t>(0x1e,    0),
  std::pair<uint16_t, uint32_t>(0x1f,    0),
  std::pair<uint16_t, uint32_t>(' ' , 6991),
  std::pair<uint16_t, uint32_t>('!' ,    0),
  std::pair<uint16_t, uint32_t>('"' ,  612),
  std::pair<uint16_t, uint32_t>('#' ,    9),
  std::pair<uint16_t, uint32_t>('$' ,    0),
  std::pair<uint16_t, uint32_t>('%' ,  123),
  std::pair<uint16_t, uint32_t>('&' ,  137),
  std::pair<uint16_t, uint32_t>('\'',    2),
  std::pair<uint16_t, uint32_t>('(' ,  187),
  std::pair<uint16_t, uint32_t>(')' ,  187),
  std::pair<uint16_t, uint32_t>('*' ,    5),
  std::pair<uint16_t, uint32_t>('+' ,  284),
  std::pair<uint16_t, uint32_t>(',' , 1613),
  std::pair<uint16_t, uint32_t>('-' , 1147),
  std::pair<uint16_t, uint32_t>('.' ,  707),
  std::pair<uint16_t, uint32_t>('/' , 1062),
  std::pair<uint16_t, uint32_t>('0' , 5583),
  std::pair<uint16_t, uint32_t>('1' , 5970),
  std::pair<uint16_t, uint32_t>('2' , 6175),
  std::pair<uint16_t, uint32_t>('3' , 3323),
  std::pair<uint16_t, uint32_t>('4' , 3148),
  std::pair<uint16_t, uint32_t>('5' , 2808),
  std::pair<uint16_t, uint32_t>('6' , 2549),
  std::pair<uint16_t, uint32_t>('7' , 2488),
  std::pair<uint16_t, uint32_t>('8' , 2755),
  std::pair<uint16_t, uint32_t>('9' , 2478),
  std::pair<uint16_t, uint32_t>(':' , 2600),
  std::pair<uint16_t, uint32_t>(';' ,  306),
  std::pair<uint16_t, uint32_t>('<' ,    0),
  std::pair<uint16_t, uint32_t>('=' , 1198),
  std::pair<uint16_t, uint32_t>('>' ,    0),
  std::pair<uint16_t, uint32_t>('?' ,   18),
  std::pair<uint16_t, uint32_t>('@' ,    0),
  std::pair<uint16_t, uint32_t>('A' , 1430),
  std::pair<uint16_t, uint32_t>('B' ,  723),
  std::pair<uint16_t, uint32_t>('C' , 1030),
  std::pair<uint16_t, uint32_t>('D' ,  923),
  std::pair<uint16_t, uint32_t>('E' ,  856),
  std::pair<uint16_t, uint32_t>('F' , 1170),
  std::pair<uint16_t, uint32_t>('G' , 1640),
  std::pair<uint16_t, uint32_t>('H' ,  421),
  std::pair<uint16_t, uint32_t>('I' ,  543),
  std::pair<uint16_t, uint32_t>('J' ,  810),
  std::pair<uint16_t, uint32_t>('K' ,  464),
  std::pair<uint16_t, uint32_t>('L' ,  477),
  std::pair<uint16_t, uint32_t>('M' , 2017),
  std::pair<uint16_t, uint32_t>('N' ,  556),
  std::pair<uint16_t, uint32_t>('O' ,  613),
  std::pair<uint16_t, uint32_t>('P' ,  541),
  std::pair<uint16_t, uint32_t>('Q' ,  458),
  std::pair<uint16_t, uint32_t>('R' ,  496),
  std::pair<uint16_t, uint32_t>('S' ,  844),
  std::pair<uint16_t, uint32_t>('T' , 2192),
  std::pair<uint16_t, uint32_t>('U' ,  539),
  std::pair<uint16_t, uint32_t>('V' ,  460),
  std::pair<uint16_t, uint32_t>('W' ,  631),
  std::pair<uint16_t, uint32_t>('X' ,  432),
  std::pair<uint16_t, uint32_t>('Y' ,  458),
  std::pair<uint16_t, uint32_t>('Z' ,  455),
  std::pair<uint16_t, uint32_t>('[' ,    2),
  std::pair<uint16_t, uint32_t>('\\',    0),
  std::pair<uint16_t, uint32_t>(']' ,    2),
  std::pair<uint16_t, uint32_t>('^' ,    0),
  std::pair<uint16_t, uint32_t>('_' ,  249),
  std::pair<uint16_t, uint32_t>('`' ,    0),
  std::pair<uint16_t, uint32_t>('a' , 2889),
  std::pair<uint16_t, uint32_t>('b' , 1679),
  std::pair<uint16_t, uint32_t>('c' , 2430),
  std::pair<uint16_t, uint32_t>('d' , 2142),
  std::pair<uint16_t, uint32_t>('e' , 3353),
  std::pair<uint16_t, uint32_t>('f' , 1421),
  std::pair<uint16_t, uint32_t>('g' , 1468),
  std::pair<uint16_t, uint32_t>('h' ,  876),
  std::pair<uint16_t, uint32_t>('i' , 1599),
  std::pair<uint16_t, uint32_t>('j' ,  525),
  std::pair<uint16_t, uint32_t>('k' ,  561),
  std::pair<uint16_t, uint32_t>('l' , 1351),
  std::pair<uint16_t, uint32_t>('m' , 1094),
  std::pair<uint16_t, uint32_t>('n' , 1982),
  std::pair<uint16_t, uint32_t>('o' , 2029),
  std::pair<uint16_t, uint32_t>('p' , 1167),
  std::pair<uint16_t, uint32_t>('q' ,  451),
  std::pair<uint16_t, uint32_t>('r' , 1556),
  std::pair<uint16_t, uint32_t>('s' , 1245),
  std::pair<uint16_t, uint32_t>('t' , 1804),
  std::pair<uint16_t, uint32_t>('u' , 2178),
  std::pair<uint16_t, uint32_t>('v' ,  679),
  std::pair<uint16_t, uint32_t>('w' ,  646),
  std::pair<uint16_t, uint32_t>('x' ,  875),
  std::pair<uint16_t, uint32_t>('y' ,  618),
  std::pair<uint16_t, uint32_t>('z' ,  463),
  std::pair<uint16_t, uint32_t>('{' ,    4),
  std::pair<uint16_t, uint32_t>('|' ,   11),
  std::pair<uint16_t, uint32_t>('}' ,    4),
  std::pair<uint16_t, uint32_t>('~' ,    0),
  std::pair<uint16_t, uint32_t>(0x7f,    0),
  std::pair<uint16_t, uint32_t>(0x80,    0),
  std::pair<uint16_t, uint32_t>(0x81,    0),
  std::pair<uint16_t, uint32_t>(0x82,    0),
  std::pair<uint16_t, uint32_t>(0x83,    0),
  std::pair<uint16_t, uint32_t>(0x84,    0),
  std::pair<uint16_t, uint32_t>(0x85,    0),
  std::pair<uint16_t, uint32_t>(0x86,    0),
  std::pair<uint16_t, uint32_t>(0x87,    0),
  std::pair<uint16_t, uint32_t>(0x88,    0),
  std::pair<uint16_t, uint32_t>(0x89,    0),
  std::pair<uint16_t, uint32_t>(0x8a,    0),
  std::pair<uint16_t, uint32_t>(0x8b,    0),
  std::pair<uint16_t, uint32_t>(0x8c,    0),
  std::pair<uint16_t, uint32_t>(0x8d,    0),
  std::pair<uint16_t, uint32_t>(0x8e,    0),
  std::pair<uint16_t, uint32_t>(0x8f,    0),
  std::pair<uint16_t, uint32_t>(0x90,    0),
  std::pair<uint16_t, uint32_t>(0x91,    0),
  std::pair<uint16_t, uint32_t>(0x92,    0),
  std::pair<uint16_t, uint32_t>(0x93,    0),
  std::pair<uint16_t, uint32_t>(0x94,    0),
  std::pair<uint16_t, uint32_t>(0x95,    0),
  std::pair<uint16_t, uint32_t>(0x96,    0),
  std::pair<uint16_t, uint32_t>(0x97,    0),
  std::pair<uint16_t, uint32_t>(0x98,    0),
  std::pair<uint16_t, uint32_t>(0x99,    0),
  std::pair<uint16_t, uint32_t>(0x9a,    0),
  std::pair<uint16_t, uint32_t>(0x9b,    0),
  std::pair<uint16_t, uint32_t>(0x9c,    0),
  std::pair<uint16_t, uint32_t>(0x9d,    0),
  std::pair<uint16_t, uint32_t>(0x9e,    0),
  std::pair<uint16_t, uint32_t>(0x9f,    0),
  std::pair<uint16_t, uint32_t>(0xa0,    0),
  std::pair<uint16_t, uint32_t>(0xa1,    0),
  std::pair<uint16_t, uint32_t>(0xa2,    0),
  std::pair<uint16_t, uint32_t>(0xa3,    0),
  std::pair<uint16_t, uint32_t>(0xa4,    0),
  std::pair<uint16_t, uint32_t>(0xa5,    0),
  std::pair<uint16_t, uint32_t>(0xa6,    0),
  std::pair<uint16_t, uint32_t>(0xa7,    0),
  std::pair<uint16_t, uint32_t>(0xa8,    0),
  std::pair<uint16_t, uint32_t>(0xa9,    0),
  std::pair<uint16_t, uint32_t>(0xaa,    0),
  std::pair<uint16_t, uint32_t>(0xab,    0),
  std::pair<uint16_t, uint32_t>(0xac,    0),
  std::pair<uint16_t, uint32_t>(0xad,    0),
  std::pair<uint16_t, uint32_t>(0xae,    0),
  std::pair<uint16_t, uint32_t>(0xaf,    0),
  std::pair<uint16_t, uint32_t>(0xb0,    0),
  std::pair<uint16_t, uint32_t>(0xb1,    0),
  std::pair<uint16_t, uint32_t>(0xb2,    0),
  std::pair<uint16_t, uint32_t>(0xb3,    0),
  std::pair<uint16_t, uint32_t>(0xb4,    0),
  std::pair<uint16_t, uint32_t>(0xb5,    0),
  std::pair<uint16_t, uint32_t>(0xb6,    0),
  std::pair<uint16_t, uint32_t>(0xb7,    0),
  std::pair<uint16_t, uint32_t>(0xb8,    0),
  std::pair<uint16_t, uint32_t>(0xb9,    0),
  std::pair<uint16_t, uint32_t>(0xba,    0),
  std::pair<uint16_t, uint32_t>(0xbb,    0),
  std::pair<uint16_t, uint32_t>(0xbc,    0),
  std::pair<uint16_t, uint32_t>(0xbd,    0),
  std::pair<uint16_t, uint32_t>(0xbe,    0),
  std::pair<uint16_t, uint32_t>(0xbf,    0),
  std::pair<uint16_t, uint32_t>(0xc0,    0),
  std::pair<uint16_t, uint32_t>(0xc1,    0),
  std::pair<uint16_t, uint32_t>(0xc2,    0),
  std::pair<uint16_t, uint32_t>(0xc3,    0),
  std::pair<uint16_t, uint32_t>(0xc4,    0),
  std::pair<uint16_t, uint32_t>(0xc5,    0),
  std::pair<uint16_t, uint32_t>(0xc6,    0),
  std::pair<uint16_t, uint32_t>(0xc7,    0),
  std::pair<uint16_t, uint32_t>(0xc8,    0),
  std::pair<uint16_t, uint32_t>(0xc9,    0),
  std::pair<uint16_t, uint32_t>(0xca,    0),
  std::pair<uint16_t, uint32_t>(0xcb,    0),
  std::pair<uint16_t, uint32_t>(0xcc,    0),
  std::pair<uint16_t, uint32_t>(0xcd,    0),
  std::pair<uint16_t, uint32_t>(0xce,    0),
  std::pair<uint16_t, uint32_t>(0xcf,    0),
  std::pair<uint16_t, uint32_t>(0xd0,    0),
  std::pair<uint16_t, uint32_t>(0xd1,    0),
  std::pair<uint16_t, uint32_t>(0xd2,    0),
  std::pair<uint16_t, uint32_t>(0xd3,    0),
  std::pair<uint16_t, uint32_t>(0xd4,    0),
  std::pair<uint16_t, uint32_t>(0xd5,    0),
  std::pair<uint16_t, uint32_t>(0xd6,    0),
  std::pair<uint16_t, uint32_t>(0xd7,    0),
  std::pair<uint16_t, uint32_t>(0xd8,    0),
  std::pair<uint16_t, uint32_t>(0xd9,    0),
  std::pair<uint16_t, uint32_t>(0xda,    0),
  std::pair<uint16_t, uint32_t>(0xdb,    0),
  std::pair<uint16_t, uint32_t>(0xdc,    0),
  std::pair<uint16_t, uint32_t>(0xdd,    0),
  std::pair<uint16_t, uint32_t>(0xde,    0),
  std::pair<uint16_t, uint32_t>(0xdf,    0),
  std::pair<uint16_t, uint32_t>(0xe0,    0),
  std::pair<uint16_t, uint32_t>(0xe1,    0),
  std::pair<uint16_t, uint32_t>(0xe2,    0),
  std::pair<uint16_t, uint32_t>(0xe3,    0),
  std::pair<uint16_t, uint32_t>(0xe4,    0),
  std::pair<uint16_t, uint32_t>(0xe5,    0),
  std::pair<uint16_t, uint32_t>(0xe6,    0),
  std::pair<uint16_t, uint32_t>(0xe7,    0),
  std::pair<uint16_t, uint32_t>(0xe8,    0),
  std::pair<uint16_t, uint32_t>(0xe9,    0),
  std::pair<uint16_t, uint32_t>(0xea,    0),
  std::pair<uint16_t, uint32_t>(0xeb,    0),
  std::pair<uint16_t, uint32_t>(0xec,    0),
  std::pair<uint16_t, uint32_t>(0xed,    0),
  std::pair<uint16_t, uint32_t>(0xee,    0),
  std::pair<uint16_t, uint32_t>(0xef,    0),
  std::pair<uint16_t, uint32_t>(0xf0,    0),
  std::pair<uint16_t, uint32_t>(0xf1,    0),
  std::pair<uint16_t, uint32_t>(0xf2,    0),
  std::pair<uint16_t, uint32_t>(0xf3,    0),
  std::pair<uint16_t, uint32_t>(0xf4,    0),
  std::pair<uint16_t, uint32_t>(0xf5,    0),
  std::pair<uint16_t, uint32_t>(0xf6,    0),
  std::pair<uint16_t, uint32_t>(0xf7,    0),
  std::pair<uint16_t, uint32_t>(0xf8,    0),
  std::pair<uint16_t, uint32_t>(0xf9,    0),
  std::pair<uint16_t, uint32_t>(0xfa,    0),
  std::pair<uint16_t, uint32_t>(0xfb,    0),
  std::pair<uint16_t, uint32_t>(0xfc,    0),
  std::pair<uint16_t, uint32_t>(0xfd,    0),
  std::pair<uint16_t, uint32_t>(0xfe,    0),
  std::pair<uint16_t, uint32_t>(0xff,    0),
  std::pair<uint16_t, uint32_t>( 256, 3874),
}
};

