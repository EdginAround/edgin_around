import random

from math import pi

from typing import Any, Dict, List, Optional

from . import actions, craft, defs, essentials, events, features, settings, tasks


class Rocks(essentials.Entity):
    CODENAME = 'rocks'
    ESSENCE = craft.Essence.ROCKS

    def __init__(self, id: defs.ActorId, position: essentials.EntityPosition) -> None:
        super().__init__(id, position)
        self.features.set_inventorable()
        self.features.set_stackable(1)

    def handle_event(self, event: events.Event) -> None:
        pass


class Gold(essentials.Entity):
    CODENAME = 'gold'
    ESSENCE = craft.Essence.GOLD

    def __init__(self, id: defs.ActorId, position: essentials.EntityPosition) -> None:
        super().__init__(id, position)
        self.features.set_inventorable()
        self.features.set_stackable(1)

    def handle_event(self, event: events.Event) -> None:
        pass


class Log(essentials.Entity):
    CODENAME = 'log'
    ESSENCE = craft.Essence.LOGS

    def __init__(self, id: defs.ActorId, position: essentials.EntityPosition) -> None:
        super().__init__(id, position)
        self.features.set_inventorable()

    def handle_event(self, event: events.Event) -> None:
        pass


class Axe(essentials.Entity):
    CODENAME = 'axe'
    ESSENCE = craft.Essence.TOOL

    def __init__(self, id: defs.ActorId, position: essentials.EntityPosition) -> None:
        super().__init__(id, position)
        self.features.set_inventorable()
        self.features.set_tool_or_weapon(
                hit_damage=10,
                chop_damage=100,
                smash_damage=20,
                attack_damage=50,
            )

    def handle_event(self, event: events.Event) -> None:
        pass


class Spruce(essentials.Entity):
    CODENAME = 'spruce'
    ESSENCE = craft.Essence.PLANT

    def __init__(self, id: defs.ActorId, position: essentials.EntityPosition) -> None:
        super().__init__(id, position)
        self.features.set_damageable(
                start_health=200,
                max_health=400,
                damage_variant=defs.DamageVariant.CHOP,
            )

    def handle_event(self, event: events.Event) -> None:
        if isinstance(event, events.DamageEvent):
            assert self.features.damageable
            is_alive = self.features.damageable.handle_damage(event.damage_amount)
            if not is_alive:
                self.task = tasks.DieAndDropTask(self.get_id(), self.generate_drops())

    def generate_drops(self) -> List[essentials.Entity]:
        assert self.position is not None
        return [Log(-1, self.position) for i in range(3)]


class Warrior(essentials.Entity):
    CODENAME = 'warrior'
    ESSENCE = craft.Essence.HERO

    def __init__(self, id: defs.ActorId, position: essentials.EntityPosition) -> None:
        super().__init__(id, position)
        self.features.set_performer()

    def handle_event(self, event: events.Event) -> None:
        if isinstance(event, events.ResumeEvent) or isinstance(event, events.FinishedEvent):
            bearing = random.uniform(-pi, pi)
            self.task = tasks.WalkTask(self.get_id(), speed=1.0, bearing=bearing, duration=1.0)


class Pirate(essentials.Entity):
    CODENAME = 'pirate'
    ESSENCE = craft.Essence.HERO

    def __init__(self, id: defs.ActorId, position: essentials.EntityPosition) -> None:
        self.task: essentials.Task
        super().__init__(id, position)
        self.features.set_inventory()
        self.features.set_eater(max_capacity=100.0, hunger_value=50.0)

    def handle_event(self, event: events.Event) -> None:
        assert self.features.inventory

        if isinstance(event, events.ConcludeEvent):
            self.task.conclude()

        elif isinstance(event, events.StopEvent) or isinstance(event, events.FinishedEvent):
            self.task = essentials.IdleTask()

        elif isinstance(event, events.StartMovingEvent):
            self.task = tasks.MovementTask(self.get_id(), speed=1.0, bearing=event.bearing)

        elif isinstance(event, events.HandActivationEvent):
            item_id = self.features.inventory.get().get_hand(event.hand)
            if item_id is not None:
                self.task = tasks.UseItemTask(self.get_id(), item_id, event.object_id, event.hand)
            else:
                self.task = tasks.PickItemTask(self.get_id(), event.object_id, event.hand)

        elif isinstance(event, events.InventorySwapEvent):
            self.task = tasks.InventorySwapTask(self.get_id(), event.hand, event.inventory_index)

        elif isinstance(event, events.CraftEvent):
            self.task = tasks.CraftTask(self.get_id(), event.assembly)

        elif isinstance(event, events.ResumeEvent):
            self.task = essentials.IdleTask()


for klass in [Rocks, Gold, Log, Axe, Spruce, Warrior, Pirate]:
    settings.ENTITIES[klass.CODENAME] = klass

