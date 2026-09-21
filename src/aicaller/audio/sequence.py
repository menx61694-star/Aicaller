from dataclasses import dataclass


class AudioSequenceError(ValueError):
    """Raised when media frames violate stream ordering."""


@dataclass
class AudioSequenceTracker:
    """Small bounded state holder for detecting gaps and duplicates.

    It does not reorder or drop frames. Recovery policy belongs to the
    realtime pipeline once packet-loss behavior is implemented.
    """

    last_sequence: int | None = None

    def observe(self, sequence_number: int | None) -> str:
        if sequence_number is None:
            return "unsequenced"
        if sequence_number < 0:
            raise AudioSequenceError("sequence number cannot be negative")
        if self.last_sequence is None:
            self.last_sequence = sequence_number
            return "first"
        if sequence_number == self.last_sequence:
            return "duplicate"
        if sequence_number < self.last_sequence:
            return "out_of_order"
        if sequence_number > self.last_sequence + 1:
            self.last_sequence = sequence_number
            return "gap"
        self.last_sequence = sequence_number
        return "in_order"
