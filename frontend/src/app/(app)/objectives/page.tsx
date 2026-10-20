import { ObjectivesBoard } from "@/features/objectives/objectives-board";

export default function HomePage() {
  return (
    <>
      <div className="intro">
        <h1>Objectives</h1>
        <p className="lede">
          What you want to get done each day, week and month. Click one to put it on your calendar.
        </p>
      </div>
      <ObjectivesBoard />
    </>
  );
}
