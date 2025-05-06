import { useStore } from "../../lib/store";

export default function QuickFacts() {
  const { quickfacts } = useStore();

  if (!quickfacts) return <div>No quick facts found</div>;

  return (
    <div className="mt-4">
      <h3 className="text-lg font-semibold mb-2">Quick Facts</h3>
      <div className="bg-gray-50 rounded-md overflow-hidden">
        <table className="w-full">
          <tbody>
            {Object.entries(quickfacts).map(([key, value]) => (
              <tr key={key} className="border-b border-gray-200 last:border-0">
                <td className="p-2 text-sm text-gray-600">{key}</td>
                <td className="p-2 text-sm font-medium text-right">
                  {String(value)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
