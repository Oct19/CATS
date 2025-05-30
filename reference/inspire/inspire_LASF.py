import serial  # 调用串口通信库
import time    # 调用时间库

# 寄存器地址说明，对应微型伺服电缸（力闭环专用）用户手册11页，3.4寄存器说明
regdict = {
    'ID'              : 0x16,   # ID
    'baudrate'        : 0x17,   # 波特率设置
    'clearErrors'     : 0x18,   # 清除故障命令
    'emergencyStop'   : 0x19,   # 急停命令
    'suspend'         : 0x1A,   # 暂停运动
    'restorePar'      : 0x1B,   # 还原参数命令
    'save'            : 0x1C,   # 保存命令
    'authority'       : 0x1D,   # 权限验证码
    'forceAct'        : 0x1E,   # 过温保护设置
    'warmUpSta'       : 0x1F,   # 回温启动设置
    'overCurproSet'   : 0X20,   # 过流保护设置
    'travelLimit'     : 0x23,   # 行程上线
    'controlModel'    : 0x25,   # 控制模式
    'outputVol'       : 0x26,   # 电机输出电压
    'targetValue'     : 0x27,   # 力控目标值（力控模式下有效）
    'targetSpeed'     : 0x28,   # 目标速度（速度模式下有效）
    'targetLocation'  : 0x29,   # 目标位置（速度、定位、伺服模式下有效）
    'actualLocation'  : 0x2A,   # 实际位置
    'current'         : 0x2B,   # 电流值，单位mA
    'actualForce'     : 0x2C,   # 实际受力值，单位：g
    'fOriginalValue'  : 0x2D,   # 力传感器原始值,范围：[0,4095]
    'actualTem'       : 0x2E,   # 实际温度值
    'faultCodes'      : 0x2F,   # 故障码
}

# 函数说明：设置串口号和波特率并且打开串口；参数：port为串口号，baudrate为波特率
def openSerial(port, baudrate):
    ser = serial.Serial() # 调用串口通信函数
    ser.port = port
    ser.baudrate = baudrate
    ser.open()            # 打开串口
    return ser

# 函数说明：读电缸状态信息；参数：id为电缸ID号
def readState(ser, id):
    bytes = [0x55, 0xAA]              # 帧头
    bytes.append(0x01)                # 数据长度
    bytes.append(id)                  # ID号
    bytes.append(0x30)                # CMD_RD_STATUS 读寄存器命令标志
    checksum = 0x00                   # 校验和初始化为0
    for i in range(2, len(bytes)):
        checksum += bytes[i]          # 对数据进行加和处理
    checksum &= 0xFF                  # 对校验和取低八位
    bytes.append(checksum)            # 低八位校验和
    ser.write(bytes)                  # 向串口写入数据
    time.sleep(0.01)                  # 延时10ms
    recv = ser.read_all()             # 从端口读字节数据
    if len(recv) == 0:                # 如果返回的数据长度为0，直接返回
        return []
    num = (recv[2] & 0xFF) - 3      # 寄存器数据所返回的数量
    val = []
    for i in range(num):
        val.append(recv[7 + i])
    print('读到的寄存器值依次为：', end='')
    for i in range(num):
        print(val[i], end=' ')
    print()

# 函数说明：写电缸寄存器操作函数；参数：id为电缸ID号，add为控制表索引，num为该帧数据的部分长度，val为所要写入寄存器的数据
def writeRegister(ser, id, add, num, val):
    bytes = [0x55, 0xAA]            # 帧头
    bytes.append(num*2 + 3)         # 帧长度
    bytes.append(id)                # ID号
    bytes.append(0x32)              # CMD_WR 写寄存器命令标志
    bytes.append(add & 0xff)        # 寄存器地址低字节
    bytes.append((add >> 8) & 0xff) # 寄存器地址高字节
    bytes.append(add & 0xff)        # 控制表索引

    for i in range(num):
        bytes.append(val[i])
    checksum = 0x00                 # 校验和初始化为0
    for i in range(2, len(bytes)):
        checksum += bytes[i]        # 对数据进行加和处理
    checksum &= 0xFF                # 对校验和取低八位
    bytes.append(checksum)          # 低八位校验和
    ser.write(bytes)                # 向串口写入数据
    time.sleep(0.01)                # 延时10ms
    ser.read_all()                  # 把返回帧读掉，不处理

# 函数说明：位置模式函数；参数：id为电缸ID号， val为设置电缸位置数据
def position(ser, id, val):
    bytes = [0x55, 0xAA]              # 帧头
    bytes.append(0x0D)                # 数据长度
    bytes.append(id)                  # ID号
    bytes.append(0x32)                # CMD_WR_REGISTER 写寄存器命令标志
    bytes.append(0x25)                # 控制模式寄存器地址低字节
    bytes.append(0x00)                # 控制模式寄存器地址高字节
    bytes.append(0x00)                # 设置控制模式为速度模式
    bytes.append(0x00)                # 设置控制模式为速度模式
    bytes.append(0x00)                # 电机输出电压寄存器，在定位模式无用
    bytes.append(0x00)                # 电机输出电压寄存器，在定位模式无用
    bytes.append(0x00)                # 力控目标值寄存器，在定位模式无用
    bytes.append(0x00)                # 力控目标值寄存器，在定位模式无用
    bytes.append(0x00)                # 目标速度寄存器
    bytes.append(0x00)                # 目标速度寄存器
    bytes.append(val & 0xff)          # 目标位置
    bytes.append((val >> 8) & 0xff)   # 目标位置
    checksum = 0x00                   # 校验和初始化为0
    for i in range(2, len(bytes)):
        checksum += bytes[i]          # 对数据进行加和处理
    checksum &= 0xFF                  # 对校验和取低八位
    bytes.append(checksum)            # 低八位校验和
    ser.write(bytes)                  # 向串口写入数据
    time.sleep(0.01)                  # 延时10ms
    ser.read_all()                    # 把返回帧读掉，不处理

# 函数说明：速度模式函数；参数：id为电缸ID号，speed为设置电缸速度， val为设置电缸位置数据
def speed(ser, id, speed, val):
    bytes = [0x55, 0xAA]              # 帧头
    bytes.append(0x0D)                # 数据长度
    bytes.append(id)                  # ID号
    bytes.append(0x32)                # CMD_WR_REGISTER 写寄存器命令标志
    bytes.append(0x25)                # 控制模式寄存器地址低字节
    bytes.append(0x00)                # 控制模式寄存器地址高字节
    bytes.append(0x02)                # 设置控制模式为速度模式
    bytes.append(0x00)                # 设置控制模式为速度模式
    bytes.append(0x00)                # 电机输出电压寄存器，在定位模式无用
    bytes.append(0x00)                # 电机输出电压寄存器，在定位模式无用
    bytes.append(0x00)                # 力控目标值寄存器，在定位模式无用
    bytes.append(0x00)                # 力控目标值寄存器，在定位模式无用
    bytes.append(speed & 0xff)        # 目标速度寄存器
    bytes.append((speed >> 8) & 0xff) # 目标速度寄存器
    bytes.append(val & 0xff)          # 目标位置
    bytes.append((val >> 8) & 0xff)   # 目标位置
    checksum = 0x00                   # 校验和初始化为0
    for i in range(2, len(bytes)):
        checksum += bytes[i]          # 对数据进行加和处理
    checksum &= 0xFF                  # 对校验和取低八位
    bytes.append(checksum)            # 低八位校验和
    ser.write(bytes)                  # 向串口写入数据
    time.sleep(0.01)                  # 延时10ms
    ser.read_all()                    # 把返回帧读掉，不处理

# 函数说明：力控模式函数；参数：id为电缸ID号， force为力控目标值
def force(ser, id, force):
    bytes = [0x55, 0xAA]              # 帧头
    bytes.append(0x0D)                # 数据长度
    bytes.append(id)                  # ID号
    bytes.append(0x32)                # CMD_WR_REGISTER 写寄存器命令标志
    bytes.append(0x25)                # 控制模式寄存器地址低字节
    bytes.append(0x00)                # 控制模式寄存器地址高字节
    bytes.append(0x03)                # 设置控制模式为力控模式
    bytes.append(0x00)                # 设置控制模式为力控模式
    bytes.append(0x00)                # 电机输出电压寄存器，在力控模式无用
    bytes.append(0x00)                # 电机输出电压寄存器，在力控模式无用
    bytes.append(force & 0xff)        # 力控目标值
    bytes.append((force >> 8) & 0xff) # 力控目标值
    checksum = 0x00                   # 校验和初始化为0
    for i in range(2, len(bytes)):
        checksum += bytes[i]          # 对数据进行加和处理
    checksum &= 0xFF                  # 对校验和取低八位
    bytes.append(checksum)            # 低八位校验和
    ser.write(bytes)                  # 向串口写入数据
    time.sleep(0.01)                  # 延时10ms
    ser.read_all()                    # 把返回帧读掉，不处理

# 函数说明：电压模式函数；参数：id为电缸ID号， val为设置电缸输出电压
def voltage(ser, id, val):
    bytes = [0x55, 0xAA]              # 帧头
    bytes.append(0x07)                # 数据长度
    bytes.append(id)                  # ID号
    bytes.append(0x32)                # CMD_WR_REGISTER 写寄存器命令标志
    bytes.append(0x25)                # 控制模式寄存器地址低字节
    bytes.append(0x00)                # 控制模式寄存器地址高字节
    bytes.append(0x04)                # 设置控制模式为电压模式
    bytes.append(0x00)                # 设置控制模式为电压模式
    bytes.append(val & 0xff)          # 电机输出电压
    bytes.append((val >> 8) & 0xff)   # 电机输出电压
    checksum = 0x00                   # 校验和初始化为0
    for i in range(2, len(bytes)):
        checksum += bytes[i]          # 对数据进行加和处理
    checksum &= 0xFF                  # 对校验和取低八位
    bytes.append(checksum)            # 低八位校验和
    ser.write(bytes)                  # 向串口写入数据
    time.sleep(0.01)                  # 延时10ms
    ser.read_all()                    # 把返回帧读掉，不处理

# 函数说明：速度力控模式函数；参数：id为电缸ID号，force为力控目标值，speed为设置电缸速度， val为设置电缸位置数据
def speedForce(ser, id, force, speed, val):
    bytes = [0x55, 0xAA]              # 帧头
    bytes.append(0x0D)                # 数据长度
    bytes.append(id)                  # ID号
    bytes.append(0x32)                # CMD_WR_REGISTER 写寄存器命令标志
    bytes.append(0x25)                # 控制模式寄存器地址低字节
    bytes.append(0x00)                # 控制模式寄存器地址高字节
    bytes.append(0x05)                # 设置控制模式为速度力控模式
    bytes.append(0x00)                # 设置控制模式为速度力控模式
    bytes.append(0x00)                # 电机输出电压寄存器，在定位模式无用
    bytes.append(0x00)                # 电机输出电压寄存器，在定位模式无用
    bytes.append(force & 0xff)        # 力控目标值寄存器
    bytes.append((force >> 8) & 0xff) # 力控目标值寄存器
    bytes.append(speed & 0xff)        # 目标速度寄存器
    bytes.append((speed >> 8) & 0xff) # 目标速度寄存器
    bytes.append(val & 0xff)          # 目标位置
    bytes.append((val >> 8) & 0xff)   # 目标位置
    checksum = 0x00                   # 校验和初始化为0
    for i in range(2, len(bytes)):
        checksum += bytes[i]          # 对数据进行加和处理
    checksum &= 0xFF                  # 对校验和取低八位
    bytes.append(checksum)            # 低八位校验和
    ser.write(bytes)                  # 向串口写入数据
    time.sleep(0.01)                  # 延时10ms
    ser.read_all()                    # 把返回帧读掉，不处理

# 函数说明：读电缸寄存器操作；参数：id为电缸ID号，add为起始地址，num为该帧数据的部分长度。
def readRegister(ser, id, add, num, mute=False):
    bytes = [0x55, 0xAA]            # 帧头
    bytes.append(num + 2)           # 帧长度
    bytes.append(id)                # id
    bytes.append(0x01)              # CMD_RD 读寄存器命令标志
    bytes.append(add)               # 控制表索引
    bytes.append(num)
    checksum = 0x00                 # 校验和赋值为0
    for i in range(2, len(bytes)):
        checksum += bytes[i]        # 对数据进行加和处理
    checksum &= 0xFF                # 对校验和取低八位
    bytes.append(checksum)          # 低八位校验和
    ser.write(bytes)                # 向串口写入数据
    time.sleep(0.01)                # 延时10ms
    recv = ser.read_all()           # 从端口读字节数据
    if len(recv) == 0:              # 如果返回的数据长度为0，直接返回
        return []
    num = (recv[2] & 0xFF) - 2      # 寄存器数据所返回的数量
    val = []
    for i in range(num):
        val.append(recv[6 + i])
    if not mute:
        print('读到的寄存器值依次为：', end='')
        for i in range(num):
            print(val[i], end=' ')
        print()
    return val

# 函数说明：查询电缸状态信息函数；参数：id为电缸ID号
def control(ser, id, num):
    bytes = [0x55, 0xAA]            # 帧头
    bytes.append(num + 2)           # 帧长度
    bytes.append(id)                # ID号
    bytes.append(0x04)              # CMD_MC 单控指令
    bytes.append(0x00)              # 参数1保留
    bytes.append(0x22)              # 查询电缸状态信息
    checksum = 0x00                 # 校验和初始化为0
    for i in range(2, len(bytes)):
        checksum += bytes[i]        # 对数据进行加和处理
    checksum &= 0xFF                # 对校验和取低八位
    bytes.append(checksum)          # 低八位校验和
    ser.write(bytes)                # 向串口写入数据
    time.sleep(0.01)                # 延时10ms
    ser.read_all()                  # 把返回帧读掉，不处理
    recv = ser.read_all()           # 从端口读字节数据
    if len(recv) == 0:              # 如果返回的数据长度为0，直接返回
        return []
    num = (recv[2] & 0xFF) - 2      # 寄存器数据所返回的数量
    val = []

# 函数功能：写入电缸位置数据函数，zeroCalibra为力传感器零位校准设置、overCurproSet为过流保护设置、tarLocatSet为目标位置设置、forceAct为过温保护设置、warmUpSta为回温启动设置
def writePosition(ser, id, str, val):
    if str == 'zeroCalibra' or str == 'overCurproSet' or str == 'tarLocatSet' or str == 'forceAct' or str == 'warmUpSta':
        val_reg = []
        for i in range(3):
          val_reg.append(val & 0xFF)
          val_reg.append((val >> 8) & 0xFF)
        writeRegister(ser, id, regdict[str], 6, val_reg)
    else:
        print('函数调用错误，正确方式：str的值为\'zeroCalibra\'/\'overCurproSet\'/\'overCurproSet\'/\'tarLocatSet\'，val为长度为1的list，值为0~1000，允许使用-1作为占位符')

# 主函数功能：首先打开串口，设置对应的端口和波特率，依次设置电缸运动位置参数
if __name__ == '__main__':
    print('打开串口！') # 打印提示字符“打开串口”
    ser = openSerial('COM4', 921600) # 改成自己的串口号和波特率，波特率默认921600
    time.sleep(1)
    print('设置电缸位置信息，-1为不设置该运动速度！')
    position(ser, 5, 0)              # ID号改为对应电缸的ID号
    time.sleep(1)
    print('设置电缸速度以及位置信息')
    speed(ser, 5, 1000,1200)    # ID号改为对应电缸的ID号
    time.sleep(1)
    print('设置电缸力控目标值，速度以及位置信息')
    speedForce(ser,5, 10, 2000, 2000)
    time.sleep(1)
    print('设置力控目标值')
#    speed(ser,1, 10)
    time.sleep(1)
    print('设置电机输出电压')
  #  voltage(ser,1, 10)
    print('读取电缸状态信息')
    readState(ser, 1)

    # time.sleep(10) # 由于力校准时间较长，请不要漏过这个sleep并尝试重新与手通讯，可能导致插件崩溃
