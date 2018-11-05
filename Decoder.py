import pigpio
import asyncio
import functools
import const

class necd:
	def __init__(self):
                self.callback = None
                self.pin_callback = None
                self.frames = list()
                self._sensor_pin = None
                self.protocol = list()
                self.protocol_id = list()

	def init(self, pi, pin):
		self.pi = pi
		self.loop = asyncio.get_event_loop()
		self._sensor_pin = pin
		print(pi)
		print(pin)

	def shutdown(self):
		self.pi.set_watchdog(self._sensor_pin, 0)
		if self.pin_callback is not None:
			self.pin_callback.cancel()
			self.pin_callback = None

	def _pin_callback_entry(self, gpio, level, tick):
		if level == 2:
			if len(self.frames) < 5:
				# Short sequence. Discard
				print("Discarding Short Sequence")
				self.pi.set_watchdog(self._sensor_pin, 0)
				self.frames = list()
				return
			# Watchdog expired.
			self.loop.call_soon_threadsafe(functools.partial(self._analyse_ir_pulses))
			self.disable()
			return

		if len(self.frames) == 0:
			# First callback. enable a 50ms watchdog.
			self.pi.set_watchdog(self._sensor_pin, 100)
		if len(self.frames) == 1:
			# First callback. enable a 50ms watchdog.
			self.pi.set_watchdog(self._sensor_pin, 100)

		self.frames.append((level, tick))

	def _try_decode_nec(self, sequence):
		# First match the header.
		header_mark = sequence[0][1]
		header_space = sequence[1][1]
		print("Testing for NEC")


		result = 0
		for i in range(2, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if space > const.NEC_HIGH_SPACE * 2:
				print("Space greater than HIGH_SPACE detected")
				break

			if not (mark > const.NEC_MARK * 0.80 and mark < const.NEC_MARK * 1.20):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if (space > const.NEC_LOW_SPACE * 0.80 and space < const.NEC_LOW_SPACE * 1.20):
				result <<= 1
			elif (space > const.NEC_HIGH_SPACE * 0.80 and space < const.NEC_HIGH_SPACE * 1.20):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				print("Bad Space Detected")
				result = None
				break

		if result == None or result == 0:
			return None

		return result


	def _try_decode_rc5(self, sequence):


		# First match the header.
		header_mark_1 = sequence[0][1]
		header_space = sequence[1][1]
		header_mark_2 = sequence[2][1]
		print("Testing for RC5")

		if not (header_mark_1 > const.RC5_SLICE * 0.80 and header_mark_1 < const.RC5_SLICE * 1.20):
			print("Header Mark Failed to match" )
			return None
		if not (header_space > const.RC5_SLICE * 0.80 and header_space < const.RC5_SLICE * 1.20):
			print("Header Space Failed to match")
			return None
		if not (header_mark_2 > const.RC5_SLICE * 0.80 and header_mark_2 < const.RC5_SLICE * 1.20):
			print("Header Mark Failed to match")
			return None

		result = 0
		result <<= 1
		change = 0
		for i in range(3, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if not ((space > const.RC5_SLICE * 0.80 and space < const.RC5_SLICE * 1.20) or (space > const.RC5_SLICE_ * 0.80 and space < const.RC5_SLICE_ * 1.20)):
				# Bad decode
				print("Bad space Detected")
				result = None
				break

			if not ((mark > const.RC5_SLICE * 0.80 and mark < const.RC5_SLICE * 1.20) or (mark > const.RC5_SLICE_ * 0.80 and mark < const.RC5_SLICE_ * 1.20)):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if ((mark > const.RC5_SLICE * 0.80 and mark < const.RC5_SLICE * 1.20) and (space > const.RC5_SLICE * 0.80 and space < const.RC5_SLICE * 1.20)):
                                if not (change):
                                        result <<= 1

                                else:
                                        result <<= 1
                                        result |= 1

			elif (space > const.RC5_SLICE_ * 0.80 and space < const.RC5_SLICE_ * 1.20):
				result <<= 1
				result |= 1
				change = 1

			elif (mark > const.RC5_SLICE_ * 0.80 and mark < const.RC5_SLICE_ * 1.20):
				result <<= 1
				change = 0
			else:
				# Bad decode.
				print("Bad timing Detected")
				result = None
				break


		if result == None or result == 0:
			return None

		return result

	def _try_decode_rc6(self, sequence):


		# First match the header.

		RC6_SLICE = 16
		RC6_SLICE_ = 32
		RC6_HEADER_MARK = 96
		RC6_HEADER_SPACE = 32

		header_mark = sequence[0][1]
		header_space = sequence[1][1]
		mark_ = sequence[2][1]
		space_ = sequence[4][1]
		print("Testing for RC6")

		if not (header_mark > RC6_HEADER_MARK * 0.80 and header_mark < RC6_HEADER_MARK * 1.20):
			print("Header Mark Failed to match" )
			return None
		if not (header_space > RC6_HEADER_SPACE * 0.80 and header_space < RC6_HEADER_SPACE * 1.20):
			print("Header Space Failed to match")
			return None
		result = 0
		result <<= 1
		change = 0
		for i in range(4, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			print(mark,"  ",space)

			if(i==10):
                                RC6_SLICE = 32
                                RC6_SLICE_ = 64

			if not ((space > RC6_SLICE * 0.80 and space < RC6_SLICE * 1.20) or (space > RC6_SLICE_ * 0.80 and space < RC6_SLICE_ * 1.20)):
				# Bad decode
				print("Bad space Detected")
				result = None
				break

			if not ((mark > RC6_SLICE * 0.80 and mark < RC6_SLICE * 1.20) or (mark > RC6_SLICE_ * 0.80 and mark < RC6_SLICE_ * 1.20)):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if ((mark > RC6_SLICE * 0.80 and mark < RC6_SLICE * 1.20) and (space > RC6_SLICE * 0.80 and space < RC6_SLICE * 1.20)):
                                if not (change):
                                        result <<= 1

                                else:
                                        result <<= 1
                                        result |= 1

			elif (space > RC6_SLICE_ * 0.80 and space < RC6_SLICE_ * 1.20):
				result <<= 1
				result |= 1
				change = 0

			elif (mark > RC6_SLICE_ * 0.80 and mark < RC6_SLICE_ * 1.20):
				result <<= 1
				change = 1
			else:
				# Bad decode.
				print("Bad timing Detected")
				result = None
				break


		if result == None or result == 0:
			return None

		return result

	def _try_decode_rcmm(self, sequence):

		# First match the header.
		header_mark = sequence[0][1]
		header_space = sequence[1][1]
		print("Testing for RCMM")

		if not (header_mark > const.RCMM_HEADER_MARK * 0.80 and header_mark < const.RCMM_HEADER_MARK * 1.20):
			print("Header Mark Failed to match: %d" % header_mark)
			return None
		if not (header_space > const.RCMM_HEADER_SPACE * 0.80 and header_space < const.RCMM_HEADER_SPACE * 1.20):
			print("Header Space Failed to match: %d" % header_space)
			return None

		result = 0
		for i in range(2, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if space > const.RCMM_SPACE3 * 2:
				print("Space greater than HIGH_SPACE detected")
				break

			if not (mark > const.RCMM_MARK * 0.80 and mark < const.RCMM_MARK * 1.20):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if (space > const.RCMM_SPACE0 * 0.80 and space < const.RCMM_SPACE0 * 1.20):
				result <<= 1
				result <<= 1

			elif (space > const.RCMM_SPACE1 * 0.80 and space < const.RCMM_SPACE1 * 1.20):
                                result <<= 1
                                result <<= 1
                                result |= 1

			elif (space > const.RCMM_SPACE2 * 0.80 and space < const.RCMM_SPACE2 * 1.20):
				result <<= 1
				result |= 1
				result <<= 1

			elif (space > const.RCMM_SPACE3 * 0.80 and space < const.RCMM_SPACE3 * 1.20):
				result <<= 1
				result |= 1
				result <<= 1
				result |= 1

			else:
				# Bad decode.
				print("Bad Space Detected")
				result = None
				break

		if result == None or result == 0:
			return None

		return result



	def _try_decode_xmp1(self, sequence):

		result = 0
		print("testing for XMP1")
		for i in range(0, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if space > const.XMP1_SPACE15 * 2 or space>const.XMP1_GAP:
				print("Space greater than HIGH_SPACE detected")
				break

			if i%16 is 0 and i is not 0:
                                continue


			if not (mark > const.XMP1_MARK * 0.80 and mark < const.XMP1_MARK * 1.20):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if (space > const.XMP1_SPACE0 * 0.80 and space < const.XMP1_SPACE0 * 1.20):

                            	result <<= 1
                            	result <<= 1
                            	result <<= 1
                            	result <<= 1

			elif (space > const.XMP1_SPACE1 * 0.80 and space < const.XMP1_SPACE1 * 1.20):

                                result <<= 1
                                result <<= 1
                                result <<= 1
                                result <<= 1
                                result |= 1

			elif (space > const.XMP1_SPACE2 * 0.80 and space < const.XMP1_SPACE2 * 1.20):

                                result <<= 1
                                result <<= 1
                                result <<= 1
                                result |= 1
                                result <<= 1


			elif (space > const.XMP1_SPACE3 * 0.80 and space < const.XMP1_SPACE3 * 1.20):

                                result <<= 1
                                result <<= 1
                                result <<= 1
                                result |= 1
                                result <<= 1
                                result |= 1

			elif (space > const.XMP1_SPACE4 * 0.80 and space < const.XMP1_SPACE4 * 1.20):

                                result <<= 1
                                result <<= 1
                                result |= 1
                                result <<= 1
                                result <<= 1

			elif (space > const.XMP1_SPACE5 * 0.80 and space < const.XMP1_SPACE5 * 1.20):

                                result <<= 1
                                result <<= 1
                                result |= 1
                                result <<= 1
                                result <<= 1
                                result |= 1

			elif (space > const.XMP1_SPACE6 * 0.80 and space < const.XMP1_SPACE6 * 1.20):

                                result <<= 1
                                result <<= 1
                                result |= 1
                                result <<= 1
                                result |= 1
                                result <<= 1

			elif (space > const.XMP1_SPACE7 * 0.80 and space < const.XMP1_SPACE7 * 1.20):

                                result <<= 1
                                result <<= 1
                                result |= 1
                                result <<= 1
                                result |= 1
                                result <<= 1
                                result |= 1

			elif (space > const.XMP1_SPACE8 * 0.80 and space < const.XMP1_SPACE8 * 1.20):

                                result <<= 1
                                result |= 1
                                result <<= 1
                                result <<= 1
                                result <<= 1

			elif (space > const.XMP1_SPACE9 * 0.80 and space < const.XMP1_SPACE9 * 1.20):

                                result <<= 1
                                result |= 1
                                result <<= 1
                                result <<= 1
                                result <<= 1
                                result |= 1

			elif (space > const.XMP1_SPACE10 * 0.80 and space < const.XMP1_SPACE10 * 1.20):

                                result <<= 1
                                result |= 1
                                result <<= 1
                                result <<= 1
                                result |= 1
                                result <<= 1

			elif (space > const.XMP1_SPACE11 * 0.80 and space < const.XMP1_SPACE11 * 1.20):
                                result <<= 1
                                result |= 1
                                result <<= 1
                                result <<= 1
                                result |= 1
                                result <<= 1
                                result |= 1

			elif (space > const.XMP1_SPACE12 * 0.80 and space < const.XMP1_SPACE12 * 1.20):
                                result <<= 1
                                result |= 1
                                result <<= 1
                                result |= 1
                                result <<= 1
                                result <<= 1

			elif (space > const.XMP1_SPACE13 * 0.80 and space < const.XMP1_SPACE13 * 1.20):

                                result <<= 1
                                result |= 1
                                result <<= 1
                                result |= 1
                                result <<= 1
                                result <<= 1
                                result |= 1

			elif (space > const.XMP1_SPACE14 * 0.80 and space < const.XMP1_SPACE14 * 1.20):

                                result <<= 1
                                result |= 1
                                result <<= 1
                                result |= 1
                                result <<= 1
                                result |= 1
                                result <<= 1

			elif (space > const.XMP1_SPACE15 * 0.80 and space < const.XMP1_SPACE15 * 1.20):

                                result <<= 1
                                result |= 1
                                result <<= 1
                                result |= 1
                                result <<= 1
                                result |= 1
                                result <<= 1
                                result |= 1

			else:
				# Bad decode.
				print("Bad Space Detected")
				result = None
				break

		if result == None or result == 0:
			return None

		return result





	def _try_decode_rc5_57(self, sequence):

		# First match the header.
		header_mark_1 = sequence[0][1]
		header_space = sequence[1][1]
		header_mark_2 = sequence[2][1]
		print("Testing for RC5_57")

		if not (header_mark_1 > const.RC5_57_SLICE * 0.80 and header_mark_1 < const.RC5_57_SLICE * 1.20):
			print("Header Mark Failed to match" )
			return None
		if not (header_space > const.RC5_57_SLICE * 0.80 and header_space < const.RC5_57_SLICE * 1.20):
			print("Header Space Failed to match")
			return None
		if not (header_mark_2 > const.RC5_57_SLICE * 0.80 and header_mark_2 < const.RC5_57_SLICE * 1.20):
			print("Header Mark Failed to match")
			return None


		result = 0
		result <<= 1
		change = 0
		for i in range(3, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if not ((space > const.RC5_57_SLICE * 0.80 and space < const.RC5_57_SLICE * 1.20) or (space > const.RC5_57_SLICE_ * 0.80 and space < const.RC5_57_SLICE_ * 1.20)):
				# Bad decode
				print("Bad space Detected")
				result = None
				break

			if not ((mark > const.RC5_57_SLICE * 0.80 and mark < const.RC5_57_SLICE * 1.20) or (mark > const.RC5_57_SLICE_ * 0.80 and mark < const.RC5_57_SLICE_ * 1.20)):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if ((mark > const.RC5_57_SLICE * 0.80 and mark < const.RC5_57_SLICE * 1.20) and (space > const.RC5_57_SLICE * 0.80 and space < const.RC5_57_SLICE * 1.20)):
                                if not (change):
                                        result <<= 1

                                else:
                                        result <<= 1
                                        result |= 1

			elif (space > const.RC5_57_SLICE_ * 0.80 and space < const.RC5_57_SLICE_ * 1.20):
				result <<= 1
				result |= 1
				change = 1

			elif (mark > const.RC5_57_SLICE_ * 0.80 and mark < const.RC5_57_SLICE_ * 1.20):
				result <<= 1
				change = 0
			else:
				# Bad decode.
				print("Bad timing Detected")
				result = None
				break


		if result == None or result == 0:
			return None

		return result

	def _try_decode_nec_short(self, sequence):

		# First match the header.
		header_mark = sequence[0][1]
		header_space = sequence[1][1]
		print("Testing for NEC_SHORT")

		if not (header_mark > const.NEC_SHORT_HEADER_MARK * 0.80 and header_mark < const.NEC_SHORT_HEADER_MARK * 1.20):
			print("Header Mark Failed to match: %d" % header_mark)
			return None
		if not (header_space > const.NEC_SHORT_HEADER_SPACE * 0.80 and header_space < const.NEC_SHORT_HEADER_SPACE * 1.20):
			print("Header Space Failed to match: %d" % header_space)
			return None

		result = 0
		for i in range(2, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if space > const.NEC_SHORT_HIGH_SPACE * 2:
				print("Space greater than HIGH_SPACE detected")
				break

			if not (mark > const.NEC_SHORT_MARK * 0.80 and mark < const.NEC_SHORT_MARK * 1.20):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if (space > const.NEC_SHORT_LOW_SPACE * 0.80 and space < const.NEC_SHORT_LOW_SPACE * 1.20):
				result <<= 1
			elif (space > const.NEC_SHORT_HIGH_SPACE * 0.80 and space < const.NEC_SHORT_HIGH_SPACE * 1.20):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				print("Bad Space Detected")
				result = None
				break

		if result == None or result == 0:
			return None

		return result

	def _try_decode_sony(self, sequence):

		# First match the header.
		header_mark = sequence[0][1]
		header_space = sequence[1][1]
		print("Testing for SONY")

		if not (header_mark > const.SONY_HEADER_MARK * 0.80 and header_mark < const.SONY_HEADER_MARK * 1.20):
			print("Header Mark Failed to match: %d" % header_mark)
			return None
		if not (header_space > const.SONY_HEADER_SPACE * 0.80 and header_space < const.SONY_HEADER_SPACE * 1.20):
			print("Header Space Failed to match: %d" % header_space)
			return None

		result = 0
		for i in range(2, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if mark > const.SONY_HIGH_MARK * 2:
				print("mark greater than HIGH_MARK detected")
				break

			if not (space > const.SONY_SPACE * 0.80 and space < const.SONY_SPACE * 1.20):
				# Bad decode
				print("Bad space Detected")
				result = None
				break

			if (mark > const.SONY_LOW_MARK * 0.80 and mark < const.SONY_LOW_MARK * 1.20):
				result <<= 1
			elif (mark > const.SONY_HIGH_MARK * 0.80 and mark < const.SONY_HIGH_MARK * 1.20):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				print("Bad mark Detected")
				result = None
				break

		if result == None or result == 0:
			return None

		return result

	def _try_decode_panasonic(self, sequence):

		# First match the header.
		header_mark = sequence[0][1]
		header_space = sequence[1][1]
		print("Testing for PANA")

		if not (header_mark > const.PANA_HEADER_MARK * 0.80 and header_mark < const.PANA_HEADER_MARK * 1.20):
			print("Header Mark Failed to match: %d" % header_mark)
			return None
		if not (header_space > const.PANA_HEADER_SPACE * 0.80 and header_space < const.PANA_HEADER_SPACE * 1.20):
			print("Header Space Failed to match: %d" % header_space)
			return None

		result = 0
		for i in range(2, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if space > const.PANA_HIGH_SPACE * 2:
				print("Space greater than HIGH_SPACE detected")
				break

			if not (mark > const.PANA_MARK * 0.80 and mark < const.PANA_MARK * 1.20):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if (space > const.PANA_LOW_SPACE * 0.80 and space < const.PANA_LOW_SPACE * 1.20):
				result <<= 1
			elif (space > const.PANA_HIGH_SPACE * 0.80 and space < const.PANA_HIGH_SPACE * 1.20):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				print("Bad Space Detected")
				result = None
				break

		if result == None or result == 0:
			return None

		return result

	def _try_decode_jvc(self, sequence):

		# First match the header.
		header_mark = sequence[0][1]
		header_space = sequence[1][1]
		print("Testing for JVC")

		if not (header_mark > const.JVC_HEADER_MARK * 0.80 and header_mark < const.JVC_HEADER_MARK * 1.20):
			print("Header Mark Failed to match: %d" % header_mark)
			return None
		if not (header_space > const.JVC_HEADER_SPACE * 0.80 and header_space < const.JVC_HEADER_SPACE * 1.20):
			print("Header Space Failed to match: %d" % header_space)
			return None

		result = 0
		for i in range(2, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if space > const.JVC_HIGH_SPACE * 2:
				print("Space greater than HIGH_SPACE detected")
				break

			if not (mark > const.JVC_MARK * 0.80 and mark < const.JVC_MARK * 1.20):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if (space > const.JVC_LOW_SPACE * 0.80 and space < const.JVC_LOW_SPACE * 1.20):
				result <<= 1
			elif (space > const.JVC_HIGH_SPACE * 0.80 and space < const.JVC_HIGH_SPACE * 1.20):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				print("Bad Space Detected")
				result = None
				break

		if result == None or result == 0:
			return None

		return result



	def _try_decode_rc5_38(self, sequence):

		# First match the header.
		header_mark_1 = sequence[0][1]
		header_space = sequence[1][1]
		header_mark_2 = sequence[2][1]
		print("Testing for RC5_38")

		if not (header_mark_1 > const.RC5_38_SLICE * 0.80 and header_mark_1 < const.RC5_38_SLICE * 1.20):
			print("Header Mark Failed to match" )
			return None
		if not (header_space > const.RC5_38_SLICE * 0.80 and header_space < const.RC5_38_SLICE * 1.20):
			print("Header Space Failed to match")
			return None
		if not (header_mark_2 > const.RC5_38_SLICE * 0.80 and header_mark_2 < const.RC5_38_SLICE * 1.20):
			print("Header Mark Failed to match")
			return None


		result = 0
		result <<= 1
		change = 0
		for i in range(3, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if not ((space > const.RC5_38_SLICE * 0.80 and space < const.RC5_38_SLICE * 1.20) or (space > const.RC5_38_SLICE_ * 0.80 and space < const.RC5_38_SLICE_ * 1.20)):
				# Bad decode
				print("Bad space Detected")
				result = None
				break

			if not ((mark > const.RC5_38_SLICE * 0.80 and mark < const.RC5_38_SLICE * 1.20) or (mark > const.RC5_38_SLICE_ * 0.80 and mark < const.RC5_38_SLICE_ * 1.20)):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if ((mark > const.RC5_38_SLICE * 0.80 and mark < const.RC5_38_SLICE * 1.20) and (space > const.RC5_38_SLICE * 0.80 and space < const.RC5_38_SLICE * 1.20)):
                                if not (change):
                                        result <<= 1

                                else:
                                        result <<= 1
                                        result |= 1

			elif (space > const.RC5_38_SLICE_ * 0.80 and space < const.RC5_38_SLICE_ * 1.20):
				result <<= 1
				result |= 1
				change = 1

			elif (mark > const.RC5_38_SLICE_ * 0.80 and mark < const.RC5_38_SLICE_ * 1.20):
				result <<= 1
				change = 0
			else:
				# Bad decode.
				print("Bad timing Detected")
				result = None
				break


		if result == None or result == 0:
			return None

		return result


	def _try_decode_sharp(self, sequence):

		result = 0
		print("Testing for SHARP")
		for i in range(0, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if (space > const.SHARP_HIGH_SPACE * 2 and space > const.SHARP_GAP_SPACE * 2):
				print("Space greater than HIGH_SPACE detected")
				break

			if not (mark > const.SHARP_MARK * 0.80 and mark < const.SHARP_MARK * 1.20):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if ((space > const.SHARP_LOW_SPACE * 0.80 and space < const.SHARP_LOW_SPACE * 1.20) or (space > const.SHARP_GAP_SPACE * 0.80 and space < const.SHARP_GAP_SPACE * 1.20)):
				result <<= 1
			elif (space > const.SHARP_HIGH_SPACE * 0.80 and space < const.SHARP_HIGH_SPACE * 1.20):
				result <<= 1
				result |= 1

			else:
				# Bad decode.
				print("Bad Space Detected")
				result = None
				break

		if result == None or result == 0:
			return None

		return result

	def _try_decode_rca_38(self, sequence):

		# First match the header.
		header_mark = sequence[0][1]
		header_space = sequence[1][1]
		print("Testing for RCA_38")

		if not (header_mark > const.RCA38_HEADER_MARK * 0.80 and header_mark < const.RCA38_HEADER_MARK * 1.20):
			print("Header Mark Failed to match: %d" % header_mark)
			return None
		if not (header_space > const.RCA38_HEADER_SPACE * 0.80 and header_space < const.RCA38_HEADER_SPACE * 1.20):
			print("Header Space Failed to match: %d" % header_space)
			return None

		result = 0
		for i in range(2, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if space > const.RCA38_HIGH_SPACE * 2:
				print("Space greater than HIGH_SPACE detected")
				break

			if not (mark > const.RCA38_MARK * 0.80 and mark < const.RCA38_MARK * 1.20):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if (space > const.RCA38_LOW_SPACE * 0.80 and space < const.RCA38_LOW_SPACE * 1.20):
				result <<= 1
			elif (space > const.RCA38_HIGH_SPACE * 0.80 and space < const.RCA38_HIGH_SPACE * 1.20):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				print("Bad Space Detected")
				result = None
				break

		if result == None or result == 0:
			return None

		return result

	def _try_decode_rca_57(self, sequence):

		# First match the header.
		header_mark = sequence[0][1]
		header_space = sequence[1][1]
		print("Testing for RCA_57")

		if not (header_mark > const.RCA57_HEADER_MARK * 0.80 and header_mark < const.RCA57_HEADER_MARK * 1.20):
			print("Header Mark Failed to match: %d" % header_mark)
			return None
		if not (header_space > const.RCA57_HEADER_SPACE * 0.80 and header_space < const.RCA57_HEADER_SPACE * 1.20):
			print("Header Space Failed to match: %d" % header_space)
			return None

		result = 0
		for i in range(2, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if space > const.RCA57_HIGH_SPACE * 2:
				print("Space greater than HIGH_SPACE detected")
				break

			if not (mark > const.RCA57_MARK * 0.80 and mark < const.RCA57_MARK * 1.20):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if (space > const.RCA57_LOW_SPACE * 0.80 and space < const.RCA57_LOW_SPACE * 1.20):
				result <<= 1
			elif (space > const.RCA57_HIGH_SPACE * 0.80 and space < const.RCA57_HIGH_SPACE * 1.20):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				print("Bad Space Detected")
				result = None
				break

		if result == None or result == 0:
			return None

		return result

	def _try_decode_mitsubishi(self, sequence):

		# First match the header.
		header_mark = sequence[0][1]
		header_space = sequence[1][1]
		print("Testing for MITSUBISHI")

		if not (header_mark > const.MITSUBISHI_HEADER_MARK * 0.80 and header_mark < const.MITSUBISHI_HEADER_MARK * 1.20):
			print("Header Mark Failed to match: %d" % header_mark)
			return None
		if not (header_space > const.MITSUBISHI_HEADER_SPACE * 0.80 and header_space < const.MITSUBISHI_HEADER_SPACE * 1.20):
			print("Header Space Failed to match: %d" % header_space)
			return None

		result = 0
		for i in range(2, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if space > const.MITSUBISHI_HIGH_SPACE * 2:
				print("Space greater than HIGH_SPACE detected")
				break

			if not (mark > const.MITSUBISHI_MARK * 0.80 and mark < const.MITSUBISHI_MARK * 1.20):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if (space > const.MITSUBISHI_LOW_SPACE * 0.80 and space < const.MITSUBISHI_LOW_SPACE * 1.20):
				result <<= 1
			elif (space > const.MITSUBISHI_HIGH_SPACE * 0.80 and space < const.MITSUBISHI_HIGH_SPACE * 1.20):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				print("Bad Space Detected")
				result = None
				break

		if result == None or result == 0:
			return None

		return result

	def _try_decode_konka(self, sequence):

		# First match the header.
		header_mark = sequence[0][1]
		header_space = sequence[1][1]
		print("Testing for KONKA")

		if not (header_mark > const.KONKA_HEADER_MARK * 0.80 and header_mark < const.KONKA_HEADER_MARK * 1.20):
			print("Header Mark Failed to match: %d" % header_mark)
			return None
		if not (header_space > const.KONKA_HEADER_SPACE * 0.80 and header_space < const.KONKA_HEADER_SPACE * 1.20):
			print("Header Space Failed to match: %d" % header_space)
			return None

		result = 0
		for i in range(2, len(sequence), 2):
			mark = sequence[i][1]
			space = sequence[i + 1][1]

			if space > const.KONKA_HIGH_SPACE * 2:
				print("Space greater than HIGH_SPACE detected")
				break

			if not (mark > const.KONKA_MARK * 0.80 and mark < const.KONKA_MARK * 1.20):
				# Bad decode
				print("Bad Mark Detected")
				result = None
				break

			if (space > const.KONKA_LOW_SPACE * 0.80 and space < const.KONKA_LOW_SPACE * 1.20):
				result <<= 1
			elif (space > const.KONKA_HIGH_SPACE * 0.80 and space < const.KONKA_HIGH_SPACE * 1.20):
				result <<= 1
				result |= 1
			else:
				# Bad decode.
				print("Bad Space Detected")
				result = None
				break

		if result == None or result == 0:
			return None

		return result

	def _decode_ir_sequence(self):
		# Signal is active low. Hence the lead in is a -ve edge
		sequence = []
		first_tick = 0
		for level, tick in self.frames:
			if level == 0:
				if len(sequence) == 0:
					sequence.append(0)
					first_tick = tick
				else:
					diff = tick - first_tick
					if diff < 0:
						diff = (4294967295 - last_tick) + tick
					sequence.append(diff)

		# Analyze the frequency.
		sum_value = 0
		num_samples = 0
		last = 0
		print(len(sequence))
		for entry in sequence:
			if entry == 0:
				continue

			diff = entry - last
			last = entry
			if diff > 100 or diff < 10:
				continue

			sum_value += diff
			num_samples += 1


		if num_samples == 0:
			print("Unable to find the frequency of the signal")
			return

		period = sum_value / num_samples
		frequency = 1000000/period


                # Allow 15% deviation from average period
		approximate_period = period * 1.15

		differences = list()
		differences.append(0)
		for i in range(1, len(sequence)):
			differences.append(sequence[i] - sequence[i-1])

		# Now summarize the differences.
		summary = list()
		current = 1
		length = 0
		for i in differences:
			if i < approximate_period:
				if current == 1:
					# Tracking a mark. Just add the length
					length += i
				else:
					# Tracking a space. Switch to tracking mark
					length -= int(period)
					summary.append((0, length))
					length = i
					current = 1
			else:
				if current == 1:
					# Tracking a mark. Switch to tracking space
					length += int(period)
					summary.append((1, length))
					length = i
					current = 0
				else:
					length += i

		# Quantize the summary.
		summary = list(map(lambda x: (x[0], int(round(x[1] / period))), summary))

		self.frequency_select(frequency,summary) #to sort out the protocols based on the frequency


		a = self.decoder(summary)

		if self.callback is not None:
			self.callback(code)

		if a ==1:
                        return 1

	def _analyse_ir_pulses(self):
		print("Analyse called")
		m = self._decode_ir_sequence()
		self.frames = list()
		if m ==1:
                        return 1

	def enable(self):
		print(self.pin_callback)

		if self.pin_callback != None:
			return

		self.frames = list()
		self.pin_callback = self.pi.callback(self._sensor_pin, pigpio.EITHER_EDGE,self._pin_callback_entry)
		print(len(self.frames))


	def disable(self):
		if self.pin_callback == None:
			return

		self.pi.set_watchdog(self._sensor_pin, 0)
		self.pin_callback.cancel()
		self.pin_callback = None

	def set_callback(self, callback):
		self.callback = callback

	def frequency_select(self,frequency,sequence):
                print(frequency)
                if frequency > 38000 * 0.97 and frequency < 38000 * 1.03:
                        self.protocol = [self._try_decode_nec(sequence),self._try_decode_xmp1(sequence),self._try_decode_nec_short(sequence),self._try_decode_panasonic(sequence),self._try_decode_jvc(sequence),self._try_decode_rc5_38(sequence),self._try_decode_sharp(sequence),self._try_decode_rca_38(sequence),self._try_decode_mitsubishi(sequence),self._try_decode_konka(sequence)]
                        self.protocol_id = [0,4,6,8,9,10,11,12,13,14,15]

                elif frequency > 36000 * 0.80 and frequency < 36000 * 1.07:
                        self.protocol = [self._try_decode_rc5(sequence),self._try_decode_rc6(sequence),self._try_decode_rcmm(sequence)]
                        self.protocol_id = [1,2,3]

                elif frequency > 40000 * 0.80 and frequency < 40000 * 1.20:
                        self.protocol = [self._try_decode_sony(sequence)]
                        self.protocol_id = [7]

                elif frequency > 57000 * 0.80 and frequency < 57000 * 1.20:
                        self.protocol = [self._try_decode_rc5_57(sequence),self._try_decode_rca_57(sequence)]
                        self.protocol_id = [5]

                else:
                        print("The frequency is not matched to any protocol")
                return

	def decoder(self,sequence):
                name = ["NEC" , "RC5" , "RC6" , "RCMM" , "XMP1" , "RC5_57" , "NEC_SHORT" , "SONY" , "PANASONIC" , "JVC" , "RC5_38" , "SHARP" , "RCA_38" , "RCA" , "MITSUBISHI" , "KONKA" ]
                for i in range (0,len(self.protocol)):
                        if self.protocol[i] is not None:
                                a = self.protocol_id[i]
                                print("The protocol detected is ",name[a])
                                print("Code: %x" % self.protocol[i])
                                return 1

