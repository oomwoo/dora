// UART library for VEX Cortex to communicate with another UART
// Use it to connect VEX Cortex e.g. to Raspberry Pi

unsigned int nXmitChars = 0;
unsigned int nRecvChars = 0;
TUARTs nCommPort = uartTwo;
	unsigned char myvalue;
	
enum LinkCommand
{
	LINK_CMD_NONE,
	LINK_CMD_MANUAL_CONTROL,
	LINK_CMD_AUTONOMOUS_CONTROL,
	LINK_CMD_START_RECORDING,
	LINK_CMD_STOP_RECORDING,
	LINK_CMD_DISCARD_CURRENT_RECORDING = 254,
	LINK_CMD_SHUTDOWN = 255
};

const char toHex[16] = { '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F' };

void QueueUartChar(char value)
{
	nXmitChars++;
	sendChar(nCommPort, value);
	while (!bXmitComplete(uartOne))
	{
		sleep(0);
	}
}

void SendUartCmd(char cmd, char value)
{
	char nibble;
	QueueUartChar(cmd);

	nibble = value >> 4;
	QueueUartChar(toHex[nibble]);

	nibble = value & 0x0f;
	QueueUartChar(toHex[nibble]);
}

void SendUartLF()
{
	QueueUartChar(0x0a);	// Line feed
}

short GetUartChar()
{
	short rcvChar;

	rcvChar = getChar(nCommPort);
	if (rcvChar != -1)
		nRecvChars++;

	return rcvChar;

}

char GetUartCharWait()
{
	short rcvChar;

	while (true)
	{
		rcvChar = GetUartChar();
		if (rcvChar == -1)
			sleep(0);
		else
			return (char) rcvChar;
	}
}

bool isValidHexChar(char ch)
{
	return ((ch >= '0' && ch <= '9') || (ch >= 'A' && ch <= 'F'));
}

char Char2Nibble(char nibble)
{
	if (nibble <= '9')
		return ((unsigned char) nibble) - '0';

	return nibble - 'A';
}

unsigned char GetUartCmd(char* value)
{
	short rcvChar;

	while (true)
	{
		rcvChar = GetUartChar();
		if (rcvChar == -1)
			return 0;

		char ch = (char) rcvChar;

		// valid command?
		if (ch >= 'a' && ch <= 'z' || ch > 'F' && ch <= 'Z')
		{
			char cmd = ch;

			char val1 = GetUartCharWait();
			if (!isValidHexChar(val1))
				return 0;

			char val2 = GetUartCharWait();
			if (!isValidHexChar(val2))
				return 0;

			char ret = GetUartCharWait();
			if (ret != '\n')
				return 0;

//			*value = Char2Nibble(val1) << 4 + Char2Nibble(val2); // ROBOT C is really buggy, cannot do this
			val1 = Char2Nibble(val1);
			val2 = Char2Nibble(val2);
			*value = val1 * 16 + val2;
			myvalue = *value;
			return cmd;
		}
	}

}
