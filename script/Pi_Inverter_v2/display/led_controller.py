#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controller LED per la matrice 8x8 del SenseHat.
UNICO proprietario del display — usa il singleton SenseHat.
Preserva tutte le animazioni originali: effetto onda, barre, gradienti.
"""

import time

from ..core.sense_hat_provider import get_sense_hat
from .. import config


class LEDController:

    def __init__(self):
        self.sense = get_sense_hat()
        self.current_grid_power = 0

    def show_message(self, message, color=None, scroll_speed=0.06):
        """Scrolla un messaggio sulla matrice LED."""
        if color is None:
            color = config.WHITE
        self.sense.show_message(message, text_colour=color, scroll_speed=scroll_speed)

    def clear(self):
        """Spegne tutti i LED."""
        self.sense.clear()

    def set_low_light(self, enabled):
        """Abilita/disabilita la modalita low-light del SenseHat."""
        self.sense.low_light = enabled

    def update_dual_bars(self, solar_level, grid_level, solar_color,
                         base_wave_speed=0.3, base_cycles=20):
        """
        Anima due barre affiancate (solar sx, grid dx) con effetto onda.
        solar_level/grid_level: 0-8. Il colore della barra rete dipende dal segno
        di current_grid_power (blu=consumo, rosso=export).
        """
        solar_ratio = max(0.1, solar_level / 8.0)
        grid_ratio = max(0.1, grid_level / 8.0)

        wave_speed = base_wave_speed * (1 - 0.7 * solar_ratio)
        cycles = int(base_cycles + 20 * solar_ratio)
        min_brightness = 0.4 - 0.2 * solar_ratio

        r, g, b = solar_color

        for cycle in range(cycles):
            for shift in range(8):
                pixels = []

                for y in range(8):

                    for x in range(4):
                        if y >= 8 - solar_level:
                            relative_pos = (y - (8 - solar_level)) / solar_level
                            wave_effect = min_brightness + (1 - min_brightness) * abs((shift - 3.5) / 3.5)
                            wave_effect = wave_effect ** (1 - 0.5 * solar_ratio)

                            if solar_ratio < 0.3:
                                new_r = int(r * wave_effect)
                                new_g = int(g * 0.7 * wave_effect * relative_pos)
                                new_b = int(b * wave_effect * 0.1)
                            elif solar_ratio < 0.6:
                                new_r = int(r * wave_effect * (1 - relative_pos * 0.5))
                                new_g = int(g * wave_effect)
                                new_b = int(b * wave_effect * 0.2)
                            else:
                                new_r = int(r * wave_effect * 0.3)
                                new_g = int(g * wave_effect)
                                new_b = int((b + 100) * wave_effect * relative_pos)

                            pixels.append((new_r, new_g, new_b))
                        else:
                            pixels.append(config.BLACK)

                    for x in range(4):
                        if y >= 8 - grid_level:
                            wave_effect = min_brightness + (1 - min_brightness) * abs((shift - 3.5) / 3.5)
                            wave_effect = wave_effect ** (1 - 0.5 * grid_ratio)

                            if self.current_grid_power >= 0:
                                new_r = int(0 * wave_effect)
                                new_g = int(0 * wave_effect)
                                new_b = int(255 * wave_effect)
                            else:
                                new_r = int(255 * wave_effect)
                                new_g = int(0 * wave_effect)
                                new_b = int(0 * wave_effect)

                            pixels.append((new_r, new_g, new_b))
                        else:
                            pixels.append(config.BLACK)

                self.sense.set_pixels(pixels)
                time.sleep(wave_speed)

    def update_single_bar(self, level, color_mode='auto',
                          base_wave_speed=0.3, base_cycles=20):
        """
        Anima una singola barra a tutta larghezza (8 colonne) con effetto onda.
        color_mode: 'blue', 'red', una tupla (r,g,b), o 'auto' (blu se consumo,
        rosso se export, in base a current_grid_power).
        """
        ratio = max(0.1, level / 8.0)
        wave_speed = base_wave_speed * (1 - 0.7 * ratio)
        cycles = int(base_cycles + 20 * ratio)
        min_brightness = 0.4 - 0.2 * ratio

        if color_mode == 'blue':
            r, g, b = (0, 0, 255)
        elif color_mode == 'red':
            r, g, b = (255, 0, 0)
        elif isinstance(color_mode, tuple):
            r, g, b = color_mode
        else:
            if self.current_grid_power >= 0:
                r, g, b = (0, 0, 255)
            else:
                r, g, b = (255, 0, 0)

        for cycle in range(cycles):
            for shift in range(8):
                pixels = []
                for y in range(8):
                    for x in range(8):
                        if y >= 8 - level:
                            wave_effect = min_brightness + (1 - min_brightness) * abs((shift - 3.5) / 3.5)
                            wave_effect = wave_effect ** (1 - 0.5 * ratio)
                            new_r = int(r * wave_effect)
                            new_g = int(g * wave_effect)
                            new_b = int(b * wave_effect)
                            pixels.append((new_r, new_g, new_b))
                        else:
                            pixels.append(config.BLACK)

                self.sense.set_pixels(pixels)
                time.sleep(wave_speed)

    def update_bar_chart(self, bar_values, color):
        """
        Disegna un grafico a barre statico (8 colonne con altezze diverse).
        bar_values: lista di 8 livelli 0-8. Colori sfumati rosso→giallo→bianco.
        """
        pixels = []
        for y in range(8):
            row = []
            for level in bar_values:
                ratio = level / 8.0
                r = int(255 * ratio)
                g = int(255 * ratio)
                b = int(255 * (1 - ratio))
                col = (r, g, b)
                if y >= 8 - level:
                    row.append(col)
                else:
                    row.append(config.BLACK)
            pixels.extend(row)
        self.sense.set_pixels(pixels)

    def calculate_level(self, current_power, historical_values):
        """
        Converte il valore corrente in un livello 0-8 per la barra,
        usando il 98esimo percentile positivo (o 2 negativo) come riferimento.
        """
        if not historical_values:
            return 8 if current_power > 0 else 0

        positive_values = [x for x in historical_values if x >= 0]
        negative_values = [x for x in historical_values if x < 0]

        if current_power >= 0:
            if not positive_values:
                return 0
            max_power = self._percentile(positive_values, 98)
            if max_power == 0:
                return 0
            level = round(current_power / max_power * 8)
            if level < 1 and current_power > 0:
                level = 1
        else:
            if not negative_values:
                return 0
            min_power = self._percentile(negative_values, 2)
            if min_power == 0:
                return 0
            level = round(abs(current_power) / abs(min_power) * 8)
            if level < 1:
                level = 1

        return min(level, 8)

    def choose_color(self, current_power, historical_values):
        """
        Sceglie il colore per la barra solare in base al rapporto corrente/max
        storico. Gradient rosso→giallo→verde.
        """
        if not historical_values:
            return config.GREEN if current_power > 0 else config.RED

        max_power = max(historical_values)
        if max_power <= 0:
            return config.RED

        ratio = max(0, min(current_power / max_power, 1))

        if ratio < 0.5:
            r = 255
            g = int(510 * ratio)
        else:
            r = int(510 * (1 - ratio))
            g = 255

        return (r, g, 0)

    def _percentile(self, values, pct):
        """Percentile pct (0-100) di una lista di valori."""
        sorted_vals = sorted(values)
        idx = int(len(sorted_vals) * pct / 100)
        return sorted_vals[min(idx, len(sorted_vals) - 1)]
