import re

# функция для того чтобы вытащить бренд машины
def get_brand_car(df):
  brand = []

  for car in df['name']:
    brand.append(car.split(' ')[0])

  return brand

# функция для парсинга столбца torque
def parsing_torque(df):  
  # регулярное выражение для чисел
  reg_num = r'([0-9]*[.,]?[0-9]+)'

  torque = [] # крутящий момент
  max_torque_rpm = [] # обороты

  for value in df['torque']:
    # приводим для удобства значения к большой строке и удаляем ',' 
    value = str(value).upper().replace(',', '')

    if value == 'NAN':
      torque.append(None)
      max_torque_rpm.append(None)
    elif 'NM' in value and 'KGM' in value:
      # 0 значение - крутящий момент в Nm
      # 2 значение - обороты
      info = re.findall(reg_num, value)

      torque.append(float(info[0]))
      max_torque_rpm.append(float(info[2]))
    elif 'NM' in value:
      if '+' in value:
        # 0 значение - крутящий момент
        # 1 значение - обороты
        # 2 значение - обороты которые надо прибавить к 1 значению
        info = re.findall(reg_num, value)

        torque.append(float(info[0]))
        max_torque_rpm.append(float(info[1]) + float(info[2]))

      elif ('-' in value or '~' in value) and '+' not in value:
        # 0 значение - крутящий момент
        # 2 значение -  максимальное значение оборотов
        info = re.findall(reg_num, value)

        torque.append(float(info[0]))
        max_torque_rpm.append(float(info[2]))

      else:
        # 0 значение - крутящий момент
        # 1 значение - обороты (может не быть)
        info = re.findall(reg_num, value)

        torque.append(float(info[0]))

        if len(info) > 1:
          max_torque_rpm.append(float(info[1]))
        else:
          max_torque_rpm.append(None)

    elif 'KGM' in value:
      if '+' in value:
        # 0 значение - крутящий момент
        # 1 значение - обороты
        # 2 значение - обороты которые надо прибавить к 1 значению
        info = re.findall(reg_num, value)

        torque.append(float(info[0]) * 9.8)
        max_torque_rpm.append(float(info[1]) + float(info[2]))

      elif ('-' in value or '~' in value) and '+' not in value:
        # 0 значение - крутящий момент
        # 2 значение -  максимальное значение оборотов
        info = re.findall(reg_num, value)

        torque.append(float(info[0]) * 9.8)
        max_torque_rpm.append(float(info[2]))

      else:
        # 0 значение - крутящий момент
        # 1 значение - обороты (может не быть)
        info = re.findall(reg_num, value)

        torque.append(float(info[0]) * 9.8)

        if len(info) > 1:
          max_torque_rpm.append(float(info[1]))
        else:
          max_torque_rpm.append(None)
    else:
      # значение в Nm и kgm но без указания единиц измерения
      if '(' in value:
        # 0 значение - крутящий момент в Nm
        # 2 значение - обороты
        info = re.findall(reg_num, value)

        torque.append(float(info[0]))
        max_torque_rpm.append(float(info[2]))
      elif '-' in value:
        # 0 значение - крутящий момент
        # 2 значение -  максимальное значение оборотов
        info = re.findall(reg_num, value)

        torque.append(float(info[0]))
        max_torque_rpm.append(float(info[2]))
      else:
        # 0 значение - крутящий момент
        # 1 значение - обороты (может не быть)
        if value == '':
          torque.append(None)
          max_torque_rpm.append(None)
        else:
          info = re.findall(reg_num, value)

          torque.append(float(info[0]))
          max_torque_rpm.append(float(info[1]))

  return torque, max_torque_rpm
