import { useState, useMemo } from 'react'
import { Search, Loader2, CheckCircle } from 'lucide-react';
import { useQuery } from 'react-query';
import { capitalizeFirstLetter } from '../../utils/helper';
import { Pagination } from 'antd'; // Import Ant Design Pagination


const fetchData = async () => {
  const response = await fetch(`${import.meta.env.VITE_API_URI}/dossier/dashboard/`);
  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  return response.json(); // Return the JSON response
};

const combineCategoriesWithStatus = (data) => {
  const submittedWithStatus = data.submitted.map(item => ({ ...item, status: 'submitted' }));
  const processingWithStatus = data.processing.map(item => ({ ...item, status: 'processing' }));
  const processedWithStatus = data.processed.map(item => ({ ...item, status: 'processed' }));

  return [
      ...submittedWithStatus,
      ...processingWithStatus,
      ...processedWithStatus
  ];
};

const calculateProcessingTime = (startDate, endDate) => {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const diffInMs = end.getTime() - start.getTime();
  
  const hours = Math.floor(diffInMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffInMs % (1000 * 60 * 60)) / (1000 * 60));
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else {
    return `${minutes} minutes`;
  }
};

const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
};

const Notification = () => {
  const { data } = useQuery(['posts'], fetchData, {
    refetchInterval: 10000,
    refetchOnWindowFocus: true,
    refetchOnMount: true
  });
  
  const dahsboardData = useMemo(() => {
    if (data) {
      return combineCategoriesWithStatus(data);
    }
    return [];
  }, [data]);

  const [searchQuery, setSearchQuery] = useState('');
  
  const filteredDiseases = dahsboardData.filter(diseases =>
    diseases?.disease.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const processingDiseases = filteredDiseases.filter(disease => disease.status === 'processing' || disease.status === 'submitted');
  const readyDiseases = filteredDiseases.filter(disease => disease.status === 'processed');

  // Pagination states for both In Progress and Ready diseases
  const [processingPage, setProcessingPage] = useState(1);
  const [readyPage, setReadyPage] = useState(1);
  const pageSize = 5; // Number of items per page

  // Handle page change for Processing diseases
  const handleProcessingPageChange = (page) => {
    setProcessingPage(page);
  };

  // Handle page change for Ready diseases
  const handleReadyPageChange = (page) => {
    setReadyPage(page);
  };

  // Paginate the processing diseases
  const paginatedProcessingDiseases = processingDiseases.slice((processingPage - 1) * pageSize, processingPage * pageSize);

  // Paginate the ready diseases
  const paginatedReadyDiseases = readyDiseases.slice((readyPage - 1) * pageSize, readyPage * pageSize);

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 min-h-[86vh]">
      <div className="mb-6">
        <div className="relative max-w-md mx-auto">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="Search diseases"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Processing Diseases Widget */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:px-6 bg-amber-50 border-b border-amber-100">
            <div className="flex items-center">
              <Loader2 className={`h-5 w-5 text-amber-500 mr-2 ${processingDiseases.length!==0 && "animate-spin"} `} />
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                In Progress ({processingDiseases.length})
              </h3>
            </div>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Disease dossiers currently being built
            </p>
          </div>
          <div className="divide-y divide-gray-200">
            {paginatedProcessingDiseases.length > 0 ? (
              paginatedProcessingDiseases.map((disease) => (
                <div key={disease.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <p className="text-base font-medium truncate">{capitalizeFirstLetter(disease.disease)}</p>
                    <div className="ml-2 flex-shrink-0 flex">
                      <p className="px-2 inline-flex text-sm leading-5 font-semibold rounded-full bg-amber-100 text-amber-800">
                        In Progress
                      </p>
                    </div>
                  </div>
                  <div className="mt-2 space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <Loader2 className="flex-shrink-0 mr-1.5 h-4 w-4 text-amber-500 animate-spin" />
                        <p className="text-sm text-gray-600">Submitted at {formatDate(disease.submission_time)}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-4 py-12 text-center text-gray-500">
                No dossiers in progress
              </div>
            )}
          </div>
         { paginatedProcessingDiseases.length > 0 && <Pagination
            current={processingPage}
            pageSize={pageSize}
            total={processingDiseases.length}
            onChange={handleProcessingPageChange}
            className="px-4 py-2"
          />}
        </div>

        {/* Ready Diseases Widget */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:px-6 bg-green-50 border-b border-green-100">
            <div className="flex items-center">
              <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Ready ({readyDiseases.length})
              </h3>
            </div>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Completed disease dossiers
            </p>
          </div>
          <div className="divide-y divide-gray-200">
            {paginatedReadyDiseases.length > 0 ? (
              paginatedReadyDiseases.map((disease) => (
                <div key={disease.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <p className="text-base font-medium truncate">{capitalizeFirstLetter(disease.disease)}</p>
                    <div className="ml-2 flex-shrink-0 flex">
                      <p className="px-2 inline-flex text-sm leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Ready
                      </p>
                    </div>
                  </div>
                  <div className="mt-2 space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <CheckCircle className="flex-shrink-0 mr-1.5 h-4 w-4 text-green-500" />
                        <p className="text-sm text-gray-600">Started at {formatDate(disease.submission_time)}</p>
                      </div>
                      <p className="text-sm font-medium text-green-600">
                        Completed in {calculateProcessingTime(disease?.submission_time, disease?.processed_time)}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-4 py-12 text-center text-gray-500">
                No completed dossiers found
              </div>
            )}
          </div>
          <Pagination
            current={readyPage}
            pageSize={pageSize}
            total={readyDiseases.length}
            onChange={handleReadyPageChange}
            className="px-4 py-2"
          />
        </div>
      </div>
    </main>
  );
};

export default Notification;
