"""A* autoplayer for the Arcade Snake game."""

from __future__ import annotations

import heapq
import itertools
import math
from collections import deque

Position = tuple[int, int]
Direction = tuple[int, int]

DIRECTIONS: tuple[Direction, ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


class SnakeAI:
    """Choose legal Snake moves using A* and a reachable-space safety rule."""

    def __init__(self, minimum_access: float = 0.60) -> None:
        """Set the minimum share of open cells that a proposed move must preserve."""
        self.minimum_access = minimum_access
        self.coverage_mode = False
        self.covered_cells: set[Position] = set()
        self.coverage_direction: Direction | None = None
        self.coverage_run = 0

    def reset(self) -> None:
        """Clear coverage progress when autopilot starts a new session."""
        self.coverage_mode = False
        self.covered_cells.clear()
        self.coverage_direction = None
        self.coverage_run = 0

    def choose_direction(
        self,
        snake: list[Position],
        food: Position,
        grid_width: int,
        grid_height: int,
        current_direction: Direction,
    ) -> Direction:
        """Choose an apple route or a long, tail-safe coverage route.

        Candidate first steps are simulated against the moving body. A* then
        searches from each candidate to the food, while flood fill checks that
        the simulated position still has enough connected open space. If no
        such food route exists, coverage mode targets the farthest reachable
        unvisited cell and rejects moves that cut off the tail.
        """
        safe_routes: list[tuple[int, int, Direction]] = []
        for direction in self._legal_directions(current_direction):
            next_head = self._add(snake[0], direction)
            eating = next_head == food
            if not self._inside(next_head, grid_width, grid_height):
                continue

            # The tail vacates its current cell unless this move eats food.
            collision_body = snake if eating else snake[:-1]
            if next_head in collision_body:
                continue

            next_snake = [next_head, *(snake if eating else snake[:-1])]
            access_count, open_count = self._reachable_space(
                next_head, next_snake, grid_width, grid_height
            )
            access_percent = access_count / max(1, open_count)
            if access_percent < self.minimum_access:
                continue

            # Replan from the simulated next position. Treat the tail as
            # available to the search when it will vacate on this move.
            blocked = set(next_snake)
            if not eating:
                blocked.discard(next_snake[-1])
            path_length = self._astar(
                next_head,
                food,
                grid_width,
                grid_height,
                blocked,
            )
            if path_length is not None:
                safe_routes.append((path_length, -access_count, direction))

        if safe_routes:
            self.coverage_mode = False
            self.coverage_direction = None
            self.coverage_run = 0
            return min(safe_routes)[2]
        if not self.coverage_mode:
            self.covered_cells.clear()
            self.coverage_direction = None
            self.coverage_run = 0
        self.coverage_mode = True
        return self._coverage_direction(
            snake, food, grid_width, grid_height, current_direction
        )

    @staticmethod
    def _legal_directions(current: Direction) -> tuple[Direction, ...]:
        """List directions other than the immediate reverse direction."""
        return tuple(direction for direction in DIRECTIONS if direction != (-current[0], -current[1]))

    @staticmethod
    def _add(position: Position, direction: Direction) -> Position:
        """Move one grid cell from a position in the given direction."""
        return position[0] + direction[0], position[1] + direction[1]

    @staticmethod
    def _inside(position: Position, width: int, height: int) -> bool:
        """Check whether a grid coordinate is within the board."""
        return 0 <= position[0] < width and 0 <= position[1] < height

    def _astar(
        self,
        start: Position,
        goal: Position,
        width: int,
        height: int,
        blocked: set[Position],
    ) -> int | None:
        """Find the shortest grid path with A*; return its length or None."""
        if start == goal:
            return 0

        frontier: list[tuple[int, int, Position]] = []
        sequence = itertools.count()
        heapq.heappush(frontier, (self._heuristic(start, goal), next(sequence), start))
        distance = {start: 0}

        while frontier:
            _, _, current = heapq.heappop(frontier)
            current_distance = distance[current]
            if current == goal:
                return current_distance

            for direction in DIRECTIONS:
                neighbor = self._add(current, direction)
                if not self._inside(neighbor, width, height):
                    continue
                if neighbor in blocked and neighbor != goal:
                    continue

                new_distance = current_distance + 1
                if new_distance >= distance.get(neighbor, math.inf):
                    continue
                distance[neighbor] = new_distance
                priority = new_distance + self._heuristic(neighbor, goal)
                heapq.heappush(frontier, (priority, next(sequence), neighbor))

        return None

    def _reachable_space(
        self,
        start: Position,
        snake: list[Position],
        width: int,
        height: int,
    ) -> tuple[int, int]:
        """Count open cells connected to the head and all currently open cells."""
        blocked = set(snake)
        available_count = width * height - len(blocked) + 1
        queue = deque([start])
        visited = {start}

        while queue:
            current = queue.popleft()
            for direction in DIRECTIONS:
                neighbor = self._add(current, direction)
                if (
                    self._inside(neighbor, width, height)
                    and neighbor not in blocked
                    and neighbor not in visited
                ):
                    visited.add(neighbor)
                    queue.append(neighbor)

        return len(visited), available_count

    def _coverage_direction(
        self,
        snake: list[Position],
        food: Position,
        width: int,
        height: int,
        current_direction: Direction,
    ) -> Direction:
        """Traverse toward the farthest reachable uncovered cell safely."""
        start = snake[0]
        self.covered_cells.add(start)

        # Find the farthest uncovered cell in the reachable area. BFS distances
        # give a long route target while still producing a valid grid path.
        blocked = set(snake[:-1])
        distances = self._bfs_distances(start, width, height, blocked)
        targets = [position for position in distances if position not in self.covered_cells]
        if not targets:
            # Begin a new pass when all currently reachable cells were visited.
            self.covered_cells = {start}
            targets = [position for position in distances if position != start]
        if not targets:
            return current_direction

        target = max(
            targets,
            key=lambda position: (
                distances[position],
                -position[1],
                -position[0],
            ),
        )

        # Compare legal first moves. Reject moves that cannot still reach the
        # tail, a standard Snake safety check that avoids entering dead ends.
        choices: list[tuple[int, int, Direction]] = []
        fallback: list[tuple[int, int, Direction]] = []
        for direction in self._legal_directions(current_direction):
            next_head = self._add(start, direction)
            eating = next_head == food
            collision_body = snake if eating else snake[:-1]
            if not self._inside(next_head, width, height) or next_head in collision_body:
                continue

            next_snake = [next_head, *(snake if eating else snake[:-1])]
            run_limit = max(2, (width if direction[0] else height) // 2)
            next_run = (
                self.coverage_run + 1
                if direction == self.coverage_direction
                else 1
            )
            if next_run > run_limit:
                continue
            if self._forms_edge_to_edge_barrier(next_snake, width, height):
                continue

            next_blocked = set(next_snake[:-1])
            access_count, _ = self._reachable_space(
                next_head, next_snake, width, height
            )

            tail = next_snake[-1]
            if self._astar(next_head, tail, width, height, next_blocked) is None:
                continue
            fallback.append((access_count, 0, direction))

            route_distances = self._bfs_distances(
                next_head, width, height, next_blocked
            )
            if target in route_distances:
                # Prefer progress along the long route, then preserve the
                # largest reachable area if multiple moves are equally short.
                choices.append((-route_distances[target], access_count, direction))

        if choices:
            selected = max(choices)[2]
            self._record_coverage_step(selected)
            return selected
        if fallback:
            selected = max(fallback)[2]
            self._record_coverage_step(selected)
            return selected
        # If no candidate reaches the chosen target, keep the run and barrier
        # limits while looking for any legal turn that remains tail-connected.
        legal_turns = []
        emergency_turns: list[tuple[int, Direction]] = []
        for direction in self._legal_directions(current_direction):
            next_head = self._add(start, direction)
            eating = next_head == food
            collision_body = snake if eating else snake[:-1]
            if not self._inside(next_head, width, height) or next_head in collision_body:
                continue
            next_snake = [next_head, *(snake if eating else snake[:-1])]
            run_limit = max(2, (width if direction[0] else height) // 2)
            next_run = self.coverage_run + 1 if direction == self.coverage_direction else 1
            if next_run > run_limit or self._forms_edge_to_edge_barrier(next_snake, width, height):
                continue
            next_blocked = set(next_snake[:-1])
            reachable_count, _ = self._reachable_space(
                next_head, next_snake, width, height
            )
            emergency_turns.append((reachable_count, direction))
            if self._astar(next_head, next_snake[-1], width, height, next_blocked) is not None:
                legal_turns.append(direction)
        if legal_turns:
            selected = legal_turns[0]
            self._record_coverage_step(selected)
            return selected
        if emergency_turns:
            selected = max(emergency_turns)[1]
            self._record_coverage_step(selected)
            return selected
        return current_direction

    def _record_coverage_step(self, direction: Direction) -> None:
        """Track straight-run length to keep coverage paths turning regularly."""
        if direction == self.coverage_direction:
            self.coverage_run += 1
        else:
            self.coverage_direction = direction
            self.coverage_run = 1

    @staticmethod
    def _forms_edge_to_edge_barrier(
        snake: list[Position], width: int, height: int
    ) -> bool:
        """Check whether the body fills a complete row or column across the map."""
        row_counts: dict[int, int] = {}
        column_counts: dict[int, int] = {}
        for x, y in set(snake):
            row_counts[y] = row_counts.get(y, 0) + 1
            column_counts[x] = column_counts.get(x, 0) + 1
        return any(count == width for count in row_counts.values()) or any(
            count == height for count in column_counts.values()
        )

    def _bfs_distances(
        self,
        start: Position,
        width: int,
        height: int,
        blocked: set[Position],
    ) -> dict[Position, int]:
        """Return shortest distances from start through currently open cells."""
        distances = {start: 0}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for direction in DIRECTIONS:
                neighbor = self._add(current, direction)
                if (
                    self._inside(neighbor, width, height)
                    and neighbor not in blocked
                    and neighbor not in distances
                ):
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)
        return distances

    @staticmethod
    def _heuristic(start: Position, goal: Position) -> int:
        """Estimate remaining path length using Manhattan distance."""
        return abs(start[0] - goal[0]) + abs(start[1] - goal[1])
