import AppHeader from "../../components/header/AppHeader";
import SearchInput from "../../components/search/SearchInput";
import ChatWindow from "../../components/search/ChatWindow";
import SourcesPanel from "../../components/search/SourcesPanel";

export default function Search() {
  return (
    <>
      <AppHeader />

      <div className="space-y-6">
        <SearchInput />

        <ChatWindow />

        <SourcesPanel />
      </div>
    </>
  );
}