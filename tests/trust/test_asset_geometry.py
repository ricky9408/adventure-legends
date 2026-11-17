from collections import deque
import itertools
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


def reachable(room, rectangles):
    width, height = room['width'], room['height']
    radius = 5
    blocked = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            if x < radius or x >= width - radius or y < radius or y >= height - radius:
                blocked[y * width + x] = 1
    for x, y, rect_width, rect_height in rectangles:
        if rect_width <= 0 or rect_height <= 0:
            raise ValueError('Collision rectangles must have positive area')
        for row in range(max(0, y - radius), min(height, y + rect_height + radius)):
            left, right = max(0, x - radius), min(width, x + rect_width + radius)
            blocked[row * width + left:row * width + right] = b'\1' * max(0, right - left)
    start_x, start_y = room['spawns']['0']
    if not (0 <= start_x < width and 0 <= start_y < height):
        raise ValueError('Spawn is outside the room')
    start = start_y * width + start_x
    if blocked[start]:
        raise ValueError('Spawn is blocked')
    seen = bytearray(width * height)
    seen[start] = 1
    pending = deque([start])
    while pending:
        current = pending.popleft()
        x, y = current % width, current // width
        for next_x, next_y in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= next_x < width and 0 <= next_y < height:
                index = next_y * width + next_x
                if not blocked[index] and not seen[index]:
                    seen[index] = 1
                    pending.append(index)
    return seen


def verify_rooms(rooms):
    checked = []
    for room in rooms:
        required = list(room['spawns'].values())
        required += [item['approach'] for item in room['exits']]
        required += [item['via'] for item in room.get('route_landmarks', [])]
        required += [point for item in room['trial_workspaces'] for point in item['walk']]
        fixtures = [item['center'] for item in room['objects']] + room['field_targets']
        fixtures += [point for item in room['trial_workspaces']
                     for point in [item['lectern'], *item['manual'], *item['targets']]]
        choices = [item['states'] for item in room['dynamic_rectangles']]
        for state in itertools.product(*choices):
            seen = reachable(room, [item['rect'] for item in room['solids']] + list(state))
            width, height = room['width'], room['height']
            for x, y in required:
                if not (0 <= x < width and 0 <= y < height and seen[y * width + x]):
                    raise ValueError(f'Room {room["id"]}: unreachable required point {(x, y)}')
            for x, y in fixtures:
                points = [(x + dx * distance, y + dy * distance)
                          for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                          for distance in range(16, 27)]
                if not any(0 <= px < width and 0 <= py < height and seen[py * width + px]
                           for px, py in points):
                    raise ValueError(f'Room {room["id"]}: fixture cannot be approached at {(x, y)}')
            checked.append({'room': room['id'], 'dynamic_rectangles': list(state)})
    return checked


class AssetGeometryTests(unittest.TestCase):
    def test_current_return_routes_and_interactions_remain_reachable_in_every_dynamic_state(self):
        rooms = json.loads((ROOT / 'assets/return_region/geometry.json').read_text())['rooms']
        self.assertTrue(rooms)
        result = verify_rooms(rooms)
        self.assertEqual({row['room'] for row in result}, {room['id'] for room in rooms})
        self.assertEqual(len(result), sum(max(1, 2 ** len(room['dynamic_rectangles'])) for room in rooms))

    def test_blocked_and_disconnected_landings_are_rejected(self):
        room = {'id': 1, 'width': 64, 'height': 64, 'spawns': {'0': [12, 12], '1': [50, 50]},
                'solids': [], 'exits': [], 'route_landmarks': [], 'trial_workspaces': [],
                'objects': [], 'field_targets': [], 'dynamic_rectangles': []}
        verify_rooms([room])
        room['solids'] = [{'rect': [0, 28, 64, 8]}]
        with self.assertRaisesRegex(ValueError, 'unreachable required point'):
            verify_rooms([room])
        room['solids'] = [{'rect': [10, 10, 8, 8]}]
        with self.assertRaisesRegex(ValueError, 'Spawn is blocked'):
            verify_rooms([room])


if __name__ == '__main__':
    unittest.main(verbosity=2)
