import math, random

from typing import List

from . import entities, essentials, geometry, state


class WorldGenerator:
    def generate_basic(self, radius) -> state.State:
        elevation_function = geometry.ElevationFunction(radius)
        entities: List[essentials.Entity] = list()
        return state.State(elevation_function, entities)

    def generate(self, radius) -> state.State:
        origin = geometry.Point(0.0, 0.0)
        elevation_function = geometry.ElevationFunction(radius)
        elevation_function.add(geometry.Hills(origin))
        elevation_function.add(geometry.Ranges(origin))
        elevation_function.add(geometry.Continents(origin))

        # Entities
        entity_list: List[essentials.Entity] = [
            entities.Axe(1, (0.501 * math.pi, -0.001 * math.pi)),
            entities.Warrior(2, (0.499 * math.pi, 0.001 * math.pi)),
            entities.Warrior(3, (0.498 * math.pi, 0.002 * math.pi)),
            entities.Rocks(4, (0.497 * math.pi, 0.003 * math.pi)),
            entities.Rocks(5, (0.495 * math.pi, 0.005 * math.pi)),
            entities.Gold(6, (0.496 * math.pi, 0.004 * math.pi)),
        ]

        for i in range(7, 100):
            phi = random.uniform(0.45 * math.pi, 0.55 * math.pi)
            theta = random.uniform(-0.05 * math.pi, 0.05 * math.pi)
            entity_list.append(entities.Spruce(i, (phi, theta)))

        return state.State(elevation_function, entity_list)

