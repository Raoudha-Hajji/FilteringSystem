import React, { useEffect, useState } from "react";
import MaterialReactTable from "material-react-table";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { useUser } from "@/contexts/UserContext";
import { Menu } from "lucide-react";
import "./TablePages.css";

const Filtered = () => {
  const { user } = useUser();
  const [data, setData] = useState([]);
  const [keywords, setKeywords] = useState([]);
  const [newKeyword, setNewKeyword] = useState("");
  const [showBanner, setShowBanner] = useState(false);
  const [newRows, setNewRows] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isKeywordsOpen, setIsKeywordsOpen] = useState(false);

  useEffect(() => {
    fetchKeywords();
    fetchData();
    const interval = setInterval(fetchData, 40 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const res = await axios.get("/sorter/api/filtered/");
      const newData = res.data;

      if (data.length > 0 && newData.length > data.length) {
        const newIds = newData.map((row) => row.id);
        const oldIds = data.map((row) => row.id);
        const addedRows = newData.filter((row) => !oldIds.includes(row.id));

        setNewRows(addedRows.map((row) => row.id));
        setShowBanner(true);
        setTimeout(() => {
          setNewRows([]);
          setShowBanner(false);
        }, 5 * 60 * 1000);
      }

      setData(newData);
    } catch (err) {
      console.error("Error fetching data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchKeywords = async () => {
    try {
      const res = await axios.get("/sorter/api/keywords/");
      setKeywords(res.data);
    } catch (err) {
      console.error("Error fetching keywords:", err);
    }
  };

  const addKeyword = async () => {
    if (!newKeyword.trim()) return;
    try {
      await axios.post("/sorter/api/keywords/", { word: newKeyword });
      setNewKeyword("");
      fetchKeywords();
      fetchData();
    } catch (err) {
      console.error("Error adding keyword:", err);
    }
  };

  const deleteKeyword = async (id) => {
    try {
      await axios.delete(`/sorter/api/keywords/${id}/`);
      fetchKeywords();
      fetchData();
    } catch (err) {
      console.error("Error deleting keyword:", err);
    }
  };

  const handleFeedback = async (id, status) => {
    try {
      await axios.post("/sorter/api/feedback/", { row_id: id, status });
      fetchData();
    } catch (err) {
      console.error("Error sending feedback:", err);
    }
  };

  const handleRefilter = async () => {
    try {
      await axios.post("/sorter/api/refilter/");
      fetchData();
    } catch (err) {
      console.error("Error triggering refilter:", err);
    }
  };

  const columns = [
    { accessorKey: "consultation_id", header: "Consultation ID" },
    { accessorKey: "date_publication", header: "Date Publication" },
    { accessorKey: "client", header: "Client" },
    { accessorKey: "intitule_projet", header: "Intitulé du projet", size: 300 },
    { accessorKey: "date_expiration", header: "Date Expiration" },
    {
      accessorKey: "lien",
      header: "Lien",
      Cell: ({ cell }) => (
        <a
          href={cell.getValue()}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-500 underline"
        >
          Ouvrir
        </a>
      ),
    },
    { accessorKey: "source", header: "Source" },
    {
      accessorKey: "status",
      header: "Status",
      Cell: ({ row }) => (
        <div className="flex gap-2">
          <Button
            onClick={() => handleFeedback(row.original.id, "keep")}
            className="bg-green-500 hover:bg-green-600 text-white"
          >
            Keep
          </Button>
          <Button
            onClick={() => handleFeedback(row.original.id, "reject")}
            className="bg-red-500 hover:bg-red-600 text-white"
          >
            Reject
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="table-wrapper">
      <div className="table-header">
        <Button
          variant="outline"
          className="menu-button"
          onClick={() => setIsKeywordsOpen(true)}
        >
          <Menu className="mr-2" /> Keywords
        </Button>
        {showBanner && (
          <div className="notification-banner">
            New filtered opportunities have been added!
          </div>
        )}
      </div>

      <div className="table-container scroll-x">
        <MaterialReactTable
          columns={columns}
          data={data}
          enablePagination
          enableGlobalFilter
          state={{ isLoading }}
          muiTableBodyRowProps={({ row }) => ({
            className: newRows.includes(row.original.id)
              ? "highlightFade"
              : "row-hover",
          })}
        />
      </div>

      {/* Slide-out keywords panel */}
      <div className={`keywords-drawer ${isKeywordsOpen ? "open" : ""}`}>
        <div className="drawer-header">
          <h3>Keywords</h3>
          <Button
            variant="outline"
            onClick={() => setIsKeywordsOpen(false)}
            className="close-button"
          >
            ✕
          </Button>
        </div>
        <ul className="keyword-list">
          {keywords.map((kw) => (
            <li key={kw.id} className="keyword-item">
              {kw.word}
              {user?.is_staff && (
                <Button
                  onClick={() => deleteKeyword(kw.id)}
                  className="delete-btn"
                >
                  ❌
                </Button>
              )}
            </li>
          ))}
        </ul>
        {user?.is_staff && (
          <div className="keyword-actions">
            <input
              type="text"
              value={newKeyword}
              onChange={(e) => setNewKeyword(e.target.value)}
              className="keyword-input"
              placeholder="Add keyword"
            />
            <Button onClick={addKeyword} className="add-btn">
              Add
            </Button>
            <Button onClick={handleRefilter} className="refilter-btn">
              Re-filter
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Filtered;
