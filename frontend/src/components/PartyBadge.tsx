import { Party } from "../types/prediction";

type Props = {
  party: Party;
};

export function PartyBadge({ party }: Props) {
  return <span className={`party-badge party-${party}`}>{party}</span>;
}
