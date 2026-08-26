"""
CSV import/export for OpenAdjust.

Supports two CSV formats:
1. Points CSV: ID;X;Y;Z;FixX;FixY;FixZ
2. Observations CSV: ID;Typ;Station;Ziel;Wert;StdDev
"""

import csv
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

from openadjust.core.network import Network
from openadjust.core.point import Point
from openadjust.models.distance import DistanceObservation
from openadjust.models.direction import DirectionObservation
from openadjust.models.zenith import ZenithObservation
from openadjust.models.levelling import LevellingObservation


def import_points_csv(filepath: str, network: Network,
                      delimiter: str = ';') -> Tuple[int, list[str]]:
    """
    Imports points from a CSV file.

    Expected format (with header):
    ID;X;Y;Z;FixX;FixY;FixZ
    P1;1000.000;2000.000;100.000;true;true;true

    Or minimal format:
    ID;X;Y;Z
    P1;1000.000;2000.000;100.000

    Args:
        filepath: Path to CSV file
        network: Network to add points to
        delimiter: CSV delimiter (default: semicolon)

    Returns:
        Tuple of (number of imported points, list of error messages)
    """
    errors = []
    count = 0

    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            # Try to detect delimiter
            sample = f.read(1024)
            f.seek(0)

            if ',' in sample and ';' not in sample:
                delimiter = ','
            elif '\t' in sample:
                delimiter = '\t'

            reader = csv.DictReader(f, delimiter=delimiter)

            for row_num, row in enumerate(reader, start=2):
                try:
                    # Normalize column names (case-insensitive)
                    row_lower = {k.lower().strip(): v for k, v in row.items()}

                    point_id = row_lower.get('id', row_lower.get('punkt', row_lower.get('name', '')))
                    if not point_id:
                        errors.append(f"Zeile {row_num}: Keine Punkt-ID gefunden")
                        continue

                    x = float(row_lower.get('x', row_lower.get('rechtswert', row_lower.get('east', 0))))
                    y = float(row_lower.get('y', row_lower.get('hochwert', row_lower.get('north', 0))))
                    z = float(row_lower.get('z', row_lower.get('höhe', row_lower.get('height', 0))))

                    # Parse fixed flags
                    def parse_bool(val):
                        if isinstance(val, bool):
                            return val
                        if isinstance(val, str):
                            return val.lower() in ('true', '1', 'ja', 'yes', 'x')
                        return bool(val)

                    fix_x = parse_bool(row_lower.get('fixx', row_lower.get('fix_x', False)))
                    fix_y = parse_bool(row_lower.get('fixy', row_lower.get('fix_y', False)))
                    fix_z = parse_bool(row_lower.get('fixz', row_lower.get('fix_z', False)))

                    point = Point(
                        id=str(point_id).strip(),
                        x=x, y=y, z=z,
                        fixed_x=fix_x, fixed_y=fix_y, fixed_z=fix_z
                    )
                    network.add_point(point)
                    count += 1

                except ValueError as e:
                    errors.append(f"Zeile {row_num}: {e}")
                except Exception as e:
                    errors.append(f"Zeile {row_num}: Unerwarteter Fehler - {e}")

    except FileNotFoundError:
        errors.append(f"Datei nicht gefunden: {filepath}")
    except Exception as e:
        errors.append(f"Fehler beim Lesen der Datei: {e}")

    return count, errors


def import_observations_csv(filepath: str, network: Network,
                            delimiter: str = ';') -> Tuple[int, list[str]]:
    """
    Imports observations from a CSV file.

    Expected format (with header):
    ID;Typ;Station;Ziel;Wert;StdDev
    D1;Strecke;P1;P2;58.310;0.002
    R1;Richtung;P1;P2;45.3456;0.0003

    Types: Strecke/Distance, Richtung/Direction, Zenitwinkel/Zenith, Höhenunterschied/Levelling

    Args:
        filepath: Path to CSV file
        network: Network to add observations to
        delimiter: CSV delimiter

    Returns:
        Tuple of (number of imported observations, list of error messages)
    """
    errors = []
    count = 0

    type_mapping = {
        'strecke': 'distance',
        'distance': 'distance',
        'dist': 'distance',
        's': 'distance',
        'richtung': 'direction',
        'direction': 'direction',
        'dir': 'direction',
        'r': 'direction',
        'hz': 'direction',
        'zenitwinkel': 'zenith',
        'zenith': 'zenith',
        'zenit': 'zenith',
        'v': 'zenith',
        'höhenunterschied': 'levelling',
        'levelling': 'levelling',
        'nivellement': 'levelling',
        'dh': 'levelling',
        'h': 'levelling'
    }

    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            sample = f.read(1024)
            f.seek(0)

            if ',' in sample and ';' not in sample:
                delimiter = ','
            elif '\t' in sample:
                delimiter = '\t'

            reader = csv.DictReader(f, delimiter=delimiter)

            for row_num, row in enumerate(reader, start=2):
                try:
                    row_lower = {k.lower().strip(): v for k, v in row.items()}

                    obs_id = row_lower.get('id', row_lower.get('name', f'OBS{count+1}'))
                    obs_type_raw = row_lower.get('typ', row_lower.get('type', 'strecke')).lower().strip()
                    obs_type = type_mapping.get(obs_type_raw, 'distance')

                    station = str(row_lower.get('station', row_lower.get('von', row_lower.get('from', '')))).strip()
                    target = str(row_lower.get('ziel', row_lower.get('target', row_lower.get('nach', row_lower.get('to', ''))))).strip()

                    if not station or not target:
                        errors.append(f"Zeile {row_num}: Station oder Ziel fehlt")
                        continue

                    # Check if points exist
                    if station not in network.points:
                        errors.append(f"Zeile {row_num}: Station '{station}' nicht gefunden")
                        continue
                    if target not in network.points:
                        errors.append(f"Zeile {row_num}: Ziel '{target}' nicht gefunden")
                        continue

                    value = float(row_lower.get('wert', row_lower.get('value', row_lower.get('messwert', 0))))
                    std_dev = float(row_lower.get('stddev', row_lower.get('std_dev', row_lower.get('sigma', 0.001))))

                    # Create observation based on type
                    if obs_type == 'distance':
                        obs = DistanceObservation(
                            id=str(obs_id), station=station, target=target,
                            value=value, std_dev=std_dev
                        )
                    elif obs_type == 'direction':
                        # Convert gon to radians if value > 2π
                        if value > 2 * np.pi:
                            value = value * np.pi / 200.0
                            std_dev = std_dev * np.pi / 200.0
                        obs = DirectionObservation(
                            id=str(obs_id), station=station, target=target,
                            value=value, std_dev=std_dev
                        )
                    elif obs_type == 'zenith':
                        if value > 2 * np.pi:
                            value = value * np.pi / 200.0
                            std_dev = std_dev * np.pi / 200.0
                        obs = ZenithObservation(
                            id=str(obs_id), station=station, target=target,
                            value=value, std_dev=std_dev
                        )
                    elif obs_type == 'levelling':
                        obs = LevellingObservation(
                            id=str(obs_id), station=station, target=target,
                            value=value, std_dev=std_dev
                        )
                    else:
                        errors.append(f"Zeile {row_num}: Unbekannter Beobachtungstyp '{obs_type_raw}'")
                        continue

                    network.add_observation(obs)
                    count += 1

                except ValueError as e:
                    errors.append(f"Zeile {row_num}: {e}")
                except Exception as e:
                    errors.append(f"Zeile {row_num}: {e}")

    except FileNotFoundError:
        errors.append(f"Datei nicht gefunden: {filepath}")
    except Exception as e:
        errors.append(f"Fehler beim Lesen der Datei: {e}")

    return count, errors


def export_points_csv(filepath: str, network: Network,
                      delimiter: str = ';') -> bool:
    """Exports points to a CSV file."""
    try:
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(['ID', 'X', 'Y', 'Z', 'FixX', 'FixY', 'FixZ'])

            for point_id, point in network.points.items():
                writer.writerow([
                    point.id,
                    f"{point.x:.4f}",
                    f"{point.y:.4f}",
                    f"{point.z:.4f}",
                    str(point.fixed_x).lower(),
                    str(point.fixed_y).lower(),
                    str(point.fixed_z).lower()
                ])
        return True
    except Exception as e:
        print(f"Error exporting points: {e}")
        return False


def export_observations_csv(filepath: str, network: Network,
                            delimiter: str = ';') -> bool:
    """Exports observations to a CSV file."""
    try:
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(['ID', 'Typ', 'Station', 'Ziel', 'Wert', 'StdDev'])

            type_names = {
                'distance': 'Strecke',
                'direction': 'Richtung',
                'zenith': 'Zenitwinkel',
                'levelling': 'Höhenunterschied'
            }

            for obs in network.observations:
                obs_type = type_names.get(obs.get_observation_type(), obs.get_observation_type())
                value = obs.value
                std_dev = obs.std_dev

                # Convert radians to gon for angles
                if obs.get_observation_type() in ['direction', 'zenith']:
                    value = value * 200.0 / np.pi
                    std_dev = std_dev * 200.0 / np.pi

                writer.writerow([
                    obs.id,
                    obs_type,
                    obs.station,
                    obs.target,
                    f"{value:.6f}",
                    f"{std_dev:.6f}"
                ])
        return True
    except Exception as e:
        print(f"Error exporting observations: {e}")
        return False
