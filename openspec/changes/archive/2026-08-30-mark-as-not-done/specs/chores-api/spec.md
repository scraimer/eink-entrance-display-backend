## ADDED Requirements

### Requirement: Chore execution reversal restores the previous chore state
The chores API SHALL support reversing the latest recorded completion for a chore. The reversal operation SHALL remove the execution record associated with the completion, restore the `chore_state` fields updated by that completion, and restore the chore's visibility in any affected stored plan snapshot so the chore appears not done again.

#### Scenario: Reversing a completion restores the chore to not done
- **WHEN** a client requests a reversal for a chore that was previously marked done
- **THEN** the execution record for that completion SHALL be removed
- **AND THEN** the affected chore SHALL appear not done again in summary responses

#### Scenario: Reversal restores the prior executor and execution date fields
- **WHEN** a client reverses a completion for a chore that had updated `last_executor_id` and `last_execution_date`
- **THEN** the chore state SHALL return to the values that were in place before that completion

#### Scenario: Reversal fails when there is no completion to undo
- **WHEN** a client requests reversal for a chore that has no reversible completion
- **THEN** the API SHALL return an error and leave the chore state unchanged
