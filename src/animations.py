import json, time

from abc import abstractmethod
from typing import Iterable, List, Optional, TYPE_CHECKING

from . import actions, defs, geometry, gui, inventory, scene, world


class AnimationName:
    IDLE = 'idle'
    WALK = 'walk'
    PICK = 'pick'
    DAMAGED = 'damaged'
    SWING_LEFT = 'swing_left'
    SWING_RIGHT = 'swing_right'


class Animation:
    def __init__(self, timeout):
        self._expired = False
        self.start_time = time.monotonic()
        self.timeout = timeout

    def expired(self) -> bool:
        if self._expired:
            return True

        elif self.timeout is not None:
            return self.start_time + self.timeout < time.monotonic()

        else:
            return False

    # If a newly added action returns an actor ID, it cancels and replaces any other action assigned
    # to the same actor.
    def get_actor_id(self) -> Optional[defs.ActorId]:
        return None

    def expire(self) -> None:
        self._expired = True

    @abstractmethod
    def tick(self, interval, scene: scene.Scene, world: world.World, gui: gui.Gui) -> None:
        raise NotImplementedError('This animation is not implemented')


class ConfigurationAnimation(Animation):
    def __init__(self, action: actions.ConfigurationAction) -> None:
        super().__init__(None)
        self.hero_actor_id = action.hero_actor_id
        self.elevation_function = action.elevation_function

    def tick(self, interval, scene: scene.Scene, world: world.World, gui: gui.Gui) -> None:
        scene.configure(self.hero_actor_id, self.elevation_function)
        self.expire()


class CraftStartAnimation(Animation):
    def __init__(self, action: actions.CraftStartAction) -> None:
        super().__init__(None)
        self.crafter_id = action.crafter_id

    def tick(self, interval, scene: scene.Scene, world: world.World, gui: gui.Gui) -> None:
        self.expire()


class CraftEndAnimation(Animation):
    def __init__(self, action: actions.CraftEndAction) -> None:
        super().__init__(None)
        self.crafter_id = action.crafter_id

    def tick(self, interval, scene: scene.Scene, world: world.World, gui: gui.Gui) -> None:
        self.expire()


class CreateActorsAnimation(Animation):
    def __init__(self, action: actions.CreateActorsAction) -> None:
        super().__init__(None)
        self.actors = action.actors

    def tick(self, interval, scene: scene.Scene, world: world.World, gui: gui.Gui) -> None:
        scene.create_actors(self.actors)
        world.create_renderers(self.actors)
        self.expire()


class DeleteActorsAnimation(Animation):
    def __init__(self, action: actions.DeleteActorsAction) -> None:
        super().__init__(None)
        self.actor_ids = action.actor_ids

    def tick(self, interval, scene: scene.Scene, world: world.World, gui: gui.Gui) -> None:
        scene.delete_actors(self.actor_ids)
        world.delete_renderers(self.actor_ids)
        self.expire()


class MovementAnimation(Animation):
    def __init__(self, action: actions.MovementAction) -> None:
        super().__init__(action.duration)
        self.actor_id = action.actor_id
        self.speed = action.speed
        self.bearing = action.bearing
        self._tick_count = 0

    def get_actor_id(self) -> defs.ActorId:
        return self.actor_id

    def tick(self, interval, scene: scene.Scene, world: world.World, gui: gui.Gui) -> None:
        distance = self.speed * interval
        actor = scene.get_actor(self.actor_id)
        actor.move_by(distance, self.bearing, scene.get_radius())
        if self._tick_count == 0:
            world.play_animation(self.actor_id, AnimationName.WALK)
        self._tick_count += 1


class LocalizeAnimation(Animation):
    def __init__(self, action: actions.LocalizeAction) -> None:
        super().__init__(None)
        self.actor_id = action.actor_id
        self.position = action.position

    def get_actor_id(self) -> defs.ActorId:
        return self.actor_id

    def tick(self, interval, scene: scene.Scene, world: world.World, gui: gui.Gui) -> None:
        actor = scene.get_actor(self.actor_id)
        if actor is not None:
            actor.set_position(self.position)
        world.play_animation(self.actor_id, AnimationName.IDLE)
        self.expire()


class StatUpdateAnimation(Animation):
    def __init__(self, action: actions.StatUpdateAction) -> None:
        super().__init__(None)
        self.actor_id = action.actor_id
        self.stats = action.stats

    def tick(self, interval, scene: scene.Scene, world: world.World, gui: gui.Gui) -> None:
        gui.set_stats(self.stats)
        self.expire()


class PickStartAnimation(Animation):
    def __init__(self, action: actions.PickStartAction) -> None:
        super().__init__(None)
        self.actor_id = action.who
        self.item_id = action.what

    def tick(self, interval, scene: scene.Scene, world: world.World, gui: gui.Gui) -> None:
        world.play_animation(self.actor_id, AnimationName.PICK)
        self.expire()


class PickEndAnimation(Animation):
    def __init__(self, action: actions.PickEndAction) -> None:
        super().__init__(None)
        self.actor_id = action.who

    def tick(self, interval, scene: scene.Scene, world: world.World, gui: gui.Gui) -> None:
        world.play_animation(self.actor_id, AnimationName.IDLE)
        self.expire()


class UpdateInventoryAnimation(Animation):
    def __init__(self, action: actions.UpdateInventoryAction) -> None:
        super().__init__(None)
        self.owner_id = action.owner_id
        self.inventory = action.inventory

    def tick(self, interval, scene: scene.Scene, world: world.World, gui: gui.Gui) -> None:
        gui.set_inventory(self.inventory)

        scene.hide_actors(self.inventory.get_all_ids())

        left_item = self.inventory.get_hand(defs.Hand.LEFT)
        world.attach_skeleton(self.owner_id, left_item, defs.Attachement.LEFT_ITEM)

        right_item = self.inventory.get_hand(defs.Hand.RIGHT)
        world.attach_skeleton(self.owner_id, right_item, defs.Attachement.RIGHT_ITEM)

        self.expire()


class DamageAnimation(Animation):
    def __init__(self, action: actions.DamageAction) -> None:
        super().__init__(None)
        self.dealer_id = action.dealer_id
        self.receiver_id = action.receiver_id
        self.variant = action.variant
        self.hand = action.hand

    def tick(self, interval, scene: scene.Scene, world: world.World, gui: gui.Gui) -> None:
        # TODO: Implement animations and play damage animation here
        if self.hand == defs.Hand.LEFT:
            world.play_animation(self.dealer_id, AnimationName.SWING_LEFT)
        else:
            world.play_animation(self.dealer_id, AnimationName.SWING_RIGHT)
        world.play_animation(self.receiver_id, AnimationName.DAMAGED)
        self.expire()


_ANIMITION_CONSTRUCTORS = {
        actions.ConfigurationAction: ConfigurationAnimation,
        actions.CraftStartAction: CraftStartAnimation,
        actions.CraftEndAction: CraftEndAnimation,
        actions.CreateActorsAction: CreateActorsAnimation,
        actions.DeleteActorsAction: DeleteActorsAnimation,
        actions.MovementAction: MovementAnimation,
        actions.LocalizeAction: LocalizeAnimation,
        actions.StatUpdateAction: StatUpdateAnimation,
        actions.PickStartAction: PickStartAnimation,
        actions.PickEndAction: PickEndAnimation,
        actions.UpdateInventoryAction: UpdateInventoryAnimation,
        actions.DamageAction: DamageAnimation,
    }

def animation_from_action(action: actions.Action) -> Optional[Animation]:
    return _ANIMITION_CONSTRUCTORS[type(action)](action)


